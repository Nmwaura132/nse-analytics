
import numpy as np
import pandas as pd
import os
import time as _time
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import logging

try:
    from history_generator import generate_stock_history
except ImportError:
    from .history_generator import generate_stock_history

try:
    from real_data_fetcher import YFinanceNSEFetcher
    _yfinance_fetcher = YFinanceNSEFetcher()
except Exception:  # yfinance not installed — degrade gracefully
    _yfinance_fetcher = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MLPredictor:
    # Models are cached per ticker for 24 h to avoid retraining on every command
    MODEL_TTL_SECONDS = 86_400

    def __init__(self):
        self.models: dict = {}          # ticker -> {model, ts, val_mse, val_rmse, val_mae, dir_acc, baseline_rmse}
        self.data_cache: dict = {}      # ticker -> DataFrame

    def get_data(
        self,
        ticker: str,
        current_price: float = 100.0,
        volatility: float = 0.02,
    ) -> pd.DataFrame:
        """
        Get historical OHLCV data for a ticker.

        Priority:
          1. Real CSV (data/history/<TICKER>.csv) — refreshed weekly from DB log
          2. StockPriceLog DB table — daily prices accumulated by the bot (Close + Volume)
          3. Yahoo Finance via yfinance (.NR suffix) — currently dead for NSE Kenya
          4. Geometric Brownian Motion simulation (labeled, for tickers with no data yet)
          5. Emergency minimum fallback

        The returned DataFrame always has a `_is_real_data` attribute set to True
        when the data comes from source 1, 2, or 3, False otherwise.  Callers can
        surface this in the UI so users know whether predictions use real prices.
        """
        ticker_upper = ticker.upper()
        df: pd.DataFrame | None = None
        is_real = False

        # --- 1. Real CSV ---
        csv_path = f"data/history/{ticker_upper}.csv"
        if os.path.exists(csv_path):
            try:
                df = pd.read_csv(csv_path)
                df['Date'] = pd.to_datetime(df['Date'])
                if not df.empty and len(df) >= 30:
                    is_real = True
                    logger.info(f"Loaded real CSV for {ticker_upper} ({len(df)} rows)")
                else:
                    df = None  # too few rows — fall through to DB
            except Exception as exc:
                logger.error(f"Failed to load CSV for {ticker_upper}: {exc}")
                df = None

        # --- 2. StockPriceLog DB ---
        if df is None:
            try:
                from download_history import from_db
                db_df = from_db(ticker_upper)
                if db_df is not None and len(db_df) >= 30:
                    db_df = db_df.reset_index()
                    df = db_df
                    is_real = True
                    logger.info(f"Loaded DB price log for {ticker_upper} ({len(df)} rows)")
            except Exception as exc:
                logger.warning(f"DB price log fetch failed for {ticker_upper}: {exc}")

        # --- 3. Yahoo Finance (real market data — currently returning 404 for .NR) ---
        if df is None and _yfinance_fetcher is not None:
            try:
                yf_df = _yfinance_fetcher.get_history(ticker_upper, period="6mo")
                if yf_df is not None and not yf_df.empty:
                    df = yf_df.reset_index()  # move Date from index to column
                    is_real = True
                    logger.info(f"Loaded yfinance data for {ticker_upper} ({len(df)} rows)")
            except Exception as exc:
                logger.warning(f"yfinance fetch failed for {ticker_upper}: {exc}")

        # --- 4. GBM Simulation (fallback, clearly labeled) ---
        if df is None:
            try:
                if ticker_upper not in self.data_cache:
                    logger.info(f"Generating GBM simulation for {ticker_upper}")
                    self.data_cache[ticker_upper] = generate_stock_history(
                        ticker_upper, current_price, volatility
                    )
                df = self.data_cache[ticker_upper]
                is_real = False
            except Exception as exc:
                logger.error(f"GBM simulation failed for {ticker_upper}: {exc}")

        # --- 5. Emergency minimum fallback ---
        if df is None or df.empty:
            logger.warning(f"Using emergency fallback data for {ticker_upper}")
            dates = pd.date_range(end=pd.Timestamp.now(), periods=30, freq='B')
            prices = [current_price * (1 + (i * 0.001) + np.random.normal(0, 0.01))
                      for i in range(30)]
            df = pd.DataFrame({'Date': dates, 'Close': prices})
            df.set_index('Date', inplace=True)
            is_real = False

        # --- Attach technical indicators ---
        try:
            df = self.add_technical_indicators(df)
        except Exception as exc:
            logger.error(f"Indicator calculation failed for {ticker_upper}: {exc}")

        # Tag real vs simulated so callers / bot UI can label correctly
        df.attrs['is_real_data'] = is_real
        df.attrs['ticker'] = ticker_upper
        return df

    def add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add RSI, MACD, Bollinger Bands to DataFrame."""
        df = df.copy()
        close = df['Close']

        # --- RSI (14) ---
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        df['RSI'] = df['RSI'].fillna(50)  # Default neutral

        # --- MACD (12, 26, 9) ---
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        df['MACD'] = ema12 - ema26
        df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['MACD_Hist'] = df['MACD'] - df['Signal_Line']

        # --- Bollinger Bands (20, 2) ---
        df['BB_Middle'] = close.rolling(window=20).mean()
        df['BB_Std'] = close.rolling(window=20).std()
        df['BB_Upper'] = df['BB_Middle'] + (2 * df['BB_Std'])
        df['BB_Lower'] = df['BB_Middle'] - (2 * df['BB_Std'])

        return df

    def analyze_trend(self, df: pd.DataFrame) -> dict:
        """
        Perform Linear Regression to determine long-term trend.
        Returns: Slope, R2, Trend Description
        """
        df = df.copy()

        # Determine Date column or index
        if 'Date' not in df.columns:
            df = df.reset_index()

        df['Ordinal'] = pd.to_datetime(df['Date']).map(pd.Timestamp.toordinal)

        X = df[['Ordinal']].values
        y = df['Close'].values

        model = LinearRegression()
        model.fit(X, y)

        slope = model.coef_[0]
        r2 = r2_score(y, model.predict(X))

        trend = "Neutral"
        if slope > 0.01: trend = "Upward"
        elif slope < -0.01: trend = "Downward"

        return {
            'slope': slope,
            'r2': r2,
            'trend': trend,
            'prediction_line': model.predict(X).tolist()
        }

    def _prepare_features(self, df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
        """
        Build ML feature matrix with shift(1) on rolling columns to prevent
        look-ahead leakage — each row uses only information available the
        previous day.

        Returns (feature_df, feature_names).
        """
        df = df.copy()
        # Shift close by 1 before computing moving averages so no future
        # price leaks into training rows via the rolling window.
        df['MA7']  = df['Close'].shift(1).rolling(window=7).mean()
        df['MA20'] = df['Close'].shift(1).rolling(window=20).mean()
        if 'Volume' in df.columns:
            df['Vol_Change'] = df['Volume'].pct_change()
        df['Price_Change'] = df['Close'].pct_change()
        df.dropna(inplace=True)

        features = ['Open', 'High', 'Low', 'Volume', 'MA7', 'MA20', 'Vol_Change']
        features = [f for f in features if f in df.columns]
        return df, features

    def walk_forward_validate(self, df: pd.DataFrame, n_splits: int = 5) -> list:
        """
        Walk-forward (expanding window) time-series cross-validation.

        Each fold trains on all data up to the split point and tests on the
        next unseen window — exactly how a live trader would operate.  This
        avoids the future-data leakage of a single shuffled train/test split.

        Args:
            df:       OHLCV DataFrame (from get_data).
            n_splits: Number of folds (default 5).

        Returns:
            List of dicts, one per fold:
              fold, train_size, test_size, rmse, mae,
              directional_accuracy, baseline_rmse, beats_baseline
        """
        df, features = self._prepare_features(df)

        X = df[features]
        y = df['Close'].shift(-1)  # target = NEXT day's close

        # Remove last row (no future label) and align
        X_all = X[:-1]
        y_all = y[:-1].dropna()
        X_all = X_all.loc[y_all.index]
        closes = df['Close'].iloc[:len(X_all)]  # current-day close, aligned

        n = len(X_all)
        min_rows = n_splits * 4
        if n < min_rows:
            return [{'error': f'Not enough data for {n_splits}-fold walk-forward '
                              f'(need ≥{min_rows} rows after feature engineering, got {n})'}]

        fold_size = n // (n_splits + 1)
        results = []

        for fold in range(n_splits):
            train_end  = fold_size * (fold + 1)
            test_start = train_end
            test_end   = min(test_start + fold_size, n)

            if test_end <= test_start:
                break

            X_train = X_all.iloc[:train_end]
            y_train = y_all.iloc[:train_end]
            X_test  = X_all.iloc[test_start:test_end]
            y_test  = y_all.iloc[test_start:test_end]
            c_test  = closes.iloc[test_start:test_end].values  # day-of closes

            model = RandomForestRegressor(n_estimators=100, random_state=42)
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)

            rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
            mae  = float(mean_absolute_error(y_test, y_pred))

            # Directional accuracy: did we get the sign of tomorrow's move right?
            actual_dir = np.sign(y_test.values - c_test)
            pred_dir   = np.sign(y_pred        - c_test)
            dir_acc    = float(np.mean(actual_dir == pred_dir)) if len(actual_dir) > 0 else 0.0

            # Persistence baseline: naive "tomorrow = today"
            baseline_rmse = float(np.sqrt(mean_squared_error(y_test.values, c_test)))

            results.append({
                'fold':                  fold + 1,
                'train_size':            train_end,
                'test_size':             test_end - test_start,
                'rmse':                  round(rmse, 4),
                'mae':                   round(mae, 4),
                'directional_accuracy':  round(dir_acc * 100, 1),
                'baseline_rmse':         round(baseline_rmse, 4),
                'beats_baseline':        rmse < baseline_rmse,
            })

        return results

    def predict_next_price(self, df: pd.DataFrame, ticker: str = "UNKNOWN") -> dict:
        """
        Use Random Forest to predict next closing price based on recent features.

        Uses a time-series train/validation split (no shuffling) so the reported
        metrics are out-of-sample rather than in-sample.  Rolling features are
        computed with a 1-day shift to prevent look-ahead leakage.

        Returns a dict with:
          predicted_price, last_close, change_forecast,
          mse, rmse, mae, mse_type,
          directional_accuracy, baseline_rmse, beats_baseline,
          is_real_data
        """
        df, features = self._prepare_features(df)

        if len(df) < 10:
            return {'error': 'Not enough data for ML prediction (need ≥10 rows)'}

        X = df[features]
        y = df['Close'].shift(-1)  # target = NEXT day's close

        # Remove last row (we want to predict it, not train on it)
        X_all = X[:-1]
        y_all = y[:-1].dropna()
        X_all = X_all.loc[y_all.index]

        if len(X_all) < 10:
            return {'error': 'Not enough valid rows after alignment'}

        # --- Time-series train / validation split (no shuffle) ---
        split = max(int(len(X_all) * 0.8), len(X_all) - 20)
        X_train, X_val = X_all.iloc[:split], X_all.iloc[split:]
        y_train, y_val = y_all.iloc[:split], y_all.iloc[split:]

        cached = self.models.get(ticker)
        model_stale = (
            cached is None
            or (_time.time() - cached['ts']) > self.MODEL_TTL_SECONDS
        )

        if model_stale:
            model = RandomForestRegressor(n_estimators=100, random_state=42)
            model.fit(X_train, y_train)

            if len(X_val) > 0:
                y_pred_val  = model.predict(X_val)
                val_mse     = float(mean_squared_error(y_val, y_pred_val))
                val_rmse    = float(np.sqrt(val_mse))
                val_mae     = float(mean_absolute_error(y_val, y_pred_val))

                # Directional accuracy on the held-out validation window
                c_val        = df['Close'].iloc[split:split + len(X_val)].values
                actual_dir   = np.sign(y_val.values - c_val)
                pred_dir     = np.sign(y_pred_val   - c_val)
                dir_acc      = float(np.mean(actual_dir == pred_dir))

                # Persistence baseline RMSE (tomorrow = today)
                baseline_rmse = float(np.sqrt(mean_squared_error(y_val.values, c_val)))
            else:
                val_mse = val_rmse = val_mae = float('nan')
                dir_acc = baseline_rmse = float('nan')

            self.models[ticker] = {
                'model':         model,
                'ts':            _time.time(),
                'val_mse':       val_mse,
                'val_rmse':      val_rmse,
                'val_mae':       val_mae,
                'dir_acc':       dir_acc,
                'baseline_rmse': baseline_rmse,
            }
        else:
            model         = cached['model']
            val_mse       = cached['val_mse']
            val_rmse      = cached.get('val_rmse', float(np.sqrt(val_mse)) if not np.isnan(cached['val_mse']) else float('nan'))
            val_mae       = cached.get('val_mae', float('nan'))
            dir_acc       = cached.get('dir_acc', float('nan'))
            baseline_rmse = cached.get('baseline_rmse', float('nan'))

        # Predict the next (future) data point using the most recent feature row
        last_row   = X.iloc[[-1]]
        prediction = float(model.predict(last_row)[0])
        last_close = float(df['Close'].iloc[-1])

        beats = (
            bool(val_rmse < baseline_rmse)
            if not (np.isnan(val_rmse) or np.isnan(baseline_rmse))
            else False
        )

        return {
            'predicted_price':       prediction,
            'last_close':            last_close,
            'change_forecast':       (prediction - last_close) / last_close,
            # Out-of-sample validation metrics
            'mse':                   val_mse,
            'mse_type':              'out_of_sample',
            'rmse':                  val_rmse,
            'mae':                   val_mae,
            'directional_accuracy':  round(dir_acc * 100, 1) if not np.isnan(dir_acc) else None,
            'baseline_rmse':         baseline_rmse,
            'beats_baseline':        beats,
            'is_real_data':          df.attrs.get('is_real_data', False),
        }

if __name__ == "__main__":
    predictor = MLPredictor()
    df = predictor.get_data("SCOM", 15.0, 0.015)

    print("--- Trend Analysis ---")
    trend = predictor.analyze_trend(df)
    print(f"Trend: {trend['trend']} (Slope: {trend['slope']:.4f}, R2: {trend['r2']:.2f})")

    print("\n--- Price Prediction (Random Forest) ---")
    forecast = predictor.predict_next_price(df, ticker="SCOM")
    print(f"Current:              {forecast['last_close']:.2f}")
    print(f"Predicted:            {forecast['predicted_price']:.2f}")
    print(f"Change:               {forecast['change_forecast']*100:.2f}%")
    print(f"RMSE (out-of-sample): {forecast['rmse']:.4f}")
    print(f"MAE  (out-of-sample): {forecast['mae']:.4f}")
    print(f"Directional accuracy: {forecast['directional_accuracy']}%")
    print(f"Persistence baseline: {forecast['baseline_rmse']:.4f}  beats_baseline={forecast['beats_baseline']}")

    print("\n--- Walk-Forward Validation (5 folds) ---")
    folds = predictor.walk_forward_validate(df, n_splits=5)
    for f in folds:
        if 'error' in f:
            print(f"  Error: {f['error']}")
        else:
            print(f"  Fold {f['fold']} | train={f['train_size']} test={f['test_size']} "
                  f"| RMSE={f['rmse']:.4f} MAE={f['mae']:.4f} "
                  f"| Dir={f['directional_accuracy']}% baseline={f['baseline_rmse']:.4f} "
                  f"beats={f['beats_baseline']}")
