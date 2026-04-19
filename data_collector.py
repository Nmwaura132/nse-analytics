"""
NSE Daily Price Collector
Scrapes AFX every day at 16:30 EAT (30 min after NSE close) and persists
to the price_history table. Also computes ML features when enough history
has accumulated (≥ 50 trading days per ticker).

Run standalone:  python data_collector.py
Or import and call start_scheduler() from nse_bot.py.
"""
import logging
import os
from datetime import date, datetime, timezone

import numpy as np
import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from data_fetcher import NSEDataFetcher
from database import MLFeatures, PriceHistory, SessionLocal

logger = logging.getLogger(__name__)

fetcher = NSEDataFetcher()


# ─── helpers ────────────────────────────────────────────────────────────────

def _upsert_price(db, ticker: str, trade_date: date, close: float,
                  volume: float, change_abs: float, change_pct: float,
                  source: str = "afx") -> bool:
    """Insert or ignore a price row (idempotent)."""
    try:
        stmt = (
            pg_insert(PriceHistory)
            .values(
                ticker=ticker, date=trade_date, close=close,
                volume=volume, change_abs=change_abs,
                change_pct=change_pct, source=source,
                created_at=datetime.now(timezone.utc),
            )
            .on_conflict_do_nothing(index_elements=["ticker", "date"])
        )
        db.execute(stmt)
        return True
    except Exception:
        # SQLite fallback (local dev) — plain insert with manual conflict skip
        exists = db.query(PriceHistory).filter_by(
            ticker=ticker, date=trade_date
        ).first()
        if not exists:
            db.add(PriceHistory(
                ticker=ticker, date=trade_date, close=close,
                volume=volume, change_abs=change_abs,
                change_pct=change_pct, source=source,
            ))
        return True


def _rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def _compute_features(ticker: str, df: pd.DataFrame) -> list[dict]:
    """Compute technical indicators from a price DataFrame.

    df must have columns: date, close, volume (sorted ascending by date).
    Returns list of dicts ready for MLFeatures upsert.
    """
    df = df.copy().sort_values("date").reset_index(drop=True)
    df["return"] = df["close"].pct_change()

    df["ma_7"] = df["close"].rolling(7).mean()
    df["ma_20"] = df["close"].rolling(20).mean()
    df["ma_50"] = df["close"].rolling(50).mean()
    df["rsi_14"] = _rsi(df["close"])

    # MACD
    ema12 = df["close"].ewm(span=12, adjust=False).mean()
    ema26 = df["close"].ewm(span=26, adjust=False).mean()
    df["macd"] = ema12 - ema26
    df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
    df["macd_hist"] = df["macd"] - df["macd_signal"]

    # Bollinger Bands (20, 2σ)
    df["bb_mid"] = df["close"].rolling(20).mean()
    bb_std = df["close"].rolling(20).std()
    df["bb_upper"] = df["bb_mid"] + 2 * bb_std
    df["bb_lower"] = df["bb_mid"] - 2 * bb_std

    df["volatility_20d"] = df["return"].rolling(20).std()
    df["volume_ma_20"] = df["volume"].rolling(20).mean()
    df["volume_ratio"] = df["volume"] / df["volume_ma_20"].replace(0, np.nan)

    # Forward returns (labels) — shift back
    df["return_1d"] = df["return"].shift(-1)
    df["return_5d"] = df["close"].pct_change(5).shift(-5)
    df["direction_5d"] = df["return_5d"].apply(
        lambda r: 1 if r > 0.01 else (-1 if r < -0.01 else 0)
        if pd.notna(r) else None
    )

    rows = []
    for _, row in df.iterrows():
        if pd.isna(row.get("ma_20")):
            continue
        rows.append({
            "ticker": ticker,
            "date": row["date"],
            "close": row["close"],
            "ma_7": row.get("ma_7"),
            "ma_20": row.get("ma_20"),
            "ma_50": row.get("ma_50"),
            "rsi_14": row.get("rsi_14"),
            "macd": row.get("macd"),
            "macd_signal": row.get("macd_signal"),
            "macd_hist": row.get("macd_hist"),
            "bb_upper": row.get("bb_upper"),
            "bb_mid": row.get("bb_mid"),
            "bb_lower": row.get("bb_lower"),
            "volatility_20d": row.get("volatility_20d"),
            "volume": row.get("volume"),
            "volume_ma_20": row.get("volume_ma_20"),
            "volume_ratio": row.get("volume_ratio"),
            "return_1d": row.get("return_1d"),
            "return_5d": row.get("return_5d"),
            "direction_5d": row.get("direction_5d"),
        })
    return rows


# ─── main jobs ───────────────────────────────────────────────────────────────

def collect_daily_prices():
    """Fetch today's closing prices for all NSE stocks and persist to DB."""
    logger.info("collect_daily_prices: starting")
    stocks = fetcher.get_all_stocks()
    if not stocks:
        logger.warning("collect_daily_prices: no stocks returned from AFX")
        return

    today = date.today()
    db = SessionLocal()
    saved = 0
    try:
        for s in stocks:
            if not s.get("price"):
                continue
            _upsert_price(
                db,
                ticker=s["ticker"],
                trade_date=today,
                close=s["price"],
                volume=s.get("volume", 0),
                change_abs=s.get("change", 0),
                change_pct=s.get("change_pct", 0),
            )
            saved += 1
        db.commit()
        logger.info(f"collect_daily_prices: saved {saved} rows for {today}")
    except Exception as e:
        db.rollback()
        logger.error(f"collect_daily_prices error: {e}")
    finally:
        db.close()


def compute_ml_features():
    """Re-compute ML features for all tickers with ≥ 50 days of history."""
    logger.info("compute_ml_features: starting")
    db = SessionLocal()
    try:
        rows = db.execute(
            select(PriceHistory.ticker).distinct()
        ).scalars().all()

        for ticker in rows:
            history = db.execute(
                select(PriceHistory)
                .where(PriceHistory.ticker == ticker)
                .order_by(PriceHistory.date)
            ).scalars().all()

            if len(history) < 50:
                continue

            df = pd.DataFrame([{
                "date": h.date, "close": h.close, "volume": h.volume
            } for h in history])

            features = _compute_features(ticker, df)
            for feat in features:
                try:
                    stmt = (
                        pg_insert(MLFeatures)
                        .values(**feat, created_at=datetime.now(timezone.utc))
                        .on_conflict_do_update(
                            index_elements=["ticker", "date"],
                            set_={k: feat[k] for k in feat
                                  if k not in ("ticker", "date")},
                        )
                    )
                    db.execute(stmt)
                except Exception:
                    # SQLite fallback
                    existing = db.query(MLFeatures).filter_by(
                        ticker=feat["ticker"], date=feat["date"]
                    ).first()
                    if existing:
                        for k, v in feat.items():
                            setattr(existing, k, v)
                    else:
                        db.add(MLFeatures(**feat))

            db.commit()
            logger.info(f"compute_ml_features: {ticker} — {len(features)} rows")

    except Exception as e:
        db.rollback()
        logger.error(f"compute_ml_features error: {e}")
    finally:
        db.close()


def seed_from_afx_history():
    """One-time seed: pull per-stock 10-day history from AFX for all tickers."""
    logger.info("seed_from_afx_history: starting")
    from data_fetcher import NSEDataFetcher as _F
    f = _F()
    companies = f.get_nse_companies()
    db = SessionLocal()
    total = 0
    try:
        for c in companies:
            ticker = c["ticker"]
            try:
                hist_df = f.get_stock_history(ticker)
                if hist_df is None or hist_df.empty:
                    continue
                for _, row in hist_df.iterrows():
                    try:
                        trade_date = pd.to_datetime(row["Date"]).date()
                    except Exception:
                        continue
                    _upsert_price(
                        db,
                        ticker=ticker,
                        trade_date=trade_date,
                        close=float(row.get("Close", 0) or 0),
                        volume=float(row.get("Volume", 0) or 0),
                        change_abs=float(row.get("Change", 0) or 0),
                        change_pct=float(row.get("Change%", 0) or 0),
                        source="afx_seed",
                    )
                    total += 1
            except Exception as e:
                logger.warning(f"seed_from_afx_history: {ticker} failed — {e}")
        db.commit()
        logger.info(f"seed_from_afx_history: inserted {total} rows")
    except Exception as e:
        db.rollback()
        logger.error(f"seed_from_afx_history error: {e}")
    finally:
        db.close()


# ─── scheduler ───────────────────────────────────────────────────────────────

def start_scheduler():
    """Start APScheduler background jobs. Call once from nse_bot.py on startup."""
    scheduler = BackgroundScheduler(timezone="Africa/Nairobi")

    # Collect prices at 16:30 EAT every weekday (NSE closes 15:00)
    scheduler.add_job(
        collect_daily_prices,
        CronTrigger(day_of_week="mon-fri", hour=16, minute=30, timezone="Africa/Nairobi"),
        id="collect_daily",
        replace_existing=True,
    )

    # Recompute ML features at 17:00 EAT every weekday (after prices collected)
    scheduler.add_job(
        compute_ml_features,
        CronTrigger(day_of_week="mon-fri", hour=17, minute=0, timezone="Africa/Nairobi"),
        id="compute_features",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("APScheduler started — daily collection at 16:30 EAT, features at 17:00 EAT")

    # Seed today's prices immediately on startup (won't duplicate due to upsert)
    import threading
    threading.Thread(target=collect_daily_prices, daemon=True).start()

    return scheduler


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Run seed then today's collection
    seed_from_afx_history()
    collect_daily_prices()
    compute_ml_features()
