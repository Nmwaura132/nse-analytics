
import numpy as np
import pandas as pd
import os
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import logging

try:
    from history_generator import generate_stock_history
except ImportError:
    # Fallback if running as script
    from .history_generator import generate_stock_history

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MLPredictor:
    def __init__(self):
        self.models = {}
        self.data_cache = {}

    def get_data(self, ticker: str, current_price: float = 100.0, volatility: float = 0.02) -> pd.DataFrame:
        """
        Get historical data for a ticker.
        Priority: 1. Real CSV Data 2. Simulation
        """
        # 1. Try loading real data
        csv_path = f"data/history/{ticker.upper()}.csv"
        df = None
        
        if os.path.exists(csv_path):
            try:
                df = pd.read_csv(csv_path)
                df['Date'] = pd.to_datetime(df['Date'])
                if not df.empty:
                    logger.info(f"Loaded real data for {ticker} from {csv_path}")
            except Exception as e:
                logger.error(f"Failed to load CSV for {ticker}: {e}")

        # 2. Fallback to simulation
        if df is None:
            try:
                if ticker not in self.data_cache:
                    logger.info(f"Generating simulation for {ticker}")
                    self.data_cache[ticker] = generate_stock_history(ticker, current_price, volatility)
                df = self.data_cache[ticker]
            except Exception as e:
                logger.error(f"Simulation failed for {ticker}: {e}")
                
        # 3. Last Resort: Emergency Data Generation (if history_generator fails)
        if df is None or df.empty:
            logger.warning(f"Using emergency fallback data for {ticker}")
            dates = pd.date_range(end=pd.Timestamp.now(), periods=10, freq='B')
            prices = [current_price]
            for _ in range(9):
                prices.append(prices[-1] * (1 + np.random.normal(0, 0.01)))
            
            df = pd.DataFrame({
                'Date': dates,
                'Close': prices[::-1], 
            })
            df['Close'] = [current_price * (1 + (i*0.001) + np.random.normal(0,0.01)) for i in range(30)]
            df.set_index('Date', inplace=True)
            
        # 4. Add Technical Indicators
        try:
            return self.add_technical_indicators(df)
        except Exception as e:
            logger.error(f"Indicator calculation failed for {ticker}: {e}")
            return df # Return raw DF if indicators fail

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

    def predict_next_price(self, df: pd.DataFrame) -> dict:
        """
        Use Random Forest to predict next closing price based on recent features.
        Features: Recent prices, Moving Averages, Volume
        """
        df = df.copy()
        
        # Feature Engineering
        df['MA7'] = df['Close'].rolling(window=7).mean()
        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['Vol_Change'] = df['Volume'].pct_change()
        df['Price_Change'] = df['Close'].pct_change()
        
        # Drop NaN from initial rolling windows
        df.dropna(inplace=True)
        
        if len(df) < 5:
            return {'error': 'Not enough data for ML prediction'}
            
        features = ['Open', 'High', 'Low', 'Volume', 'MA7', 'MA20', 'Vol_Change']
        X = df[features]
        y = df['Close'].shift(-1) # Target is NEXT day's close
        
        # Remove last row since we don't have target for it yet (that's what we want to predict)
        X_train = X[:-1]
        y_train = y[:-1]
        
        # Train
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)
        
        # Predict for the latest data point (tomorrow)
        last_row = X.iloc[[-1]]
        prediction = model.predict(last_row)[0]
        
        # Self-evaluation on training set (simplified)
        y_pred_train = model.predict(X_train)
        mse = mean_squared_error(y_train, y_pred_train)
        
        return {
            'predicted_price': prediction,
            'mse': mse,
            'last_close': df['Close'].iloc[-1],
            'change_forecast': (prediction - df['Close'].iloc[-1]) / df['Close'].iloc[-1]
        }

if __name__ == "__main__":
    predictor = MLPredictor()
    df = predictor.get_data("SCOM", 15.0, 0.015)
    
    print("--- Trend Analysis ---")
    trend = predictor.analyze_trend(df)
    print(f"Trend: {trend['trend']} (Slope: {trend['slope']:.4f}, R2: {trend['r2']:.2f})")
    
    print("\n--- Price Prediction (Random Forest) ---")
    forecast = predictor.predict_next_price(df)
    print(f"Current: {forecast['last_close']:.2f}")
    print(f"Predicted: {forecast['predicted_price']:.2f}")
    print(f"Change: {forecast['change_forecast']*100:.2f}%")
