"""
NSE Historical Data Downloader
Builds data/history/*.csv from two sources (in priority order):
  1. StockPriceLog DB table — accumulated from RapidAPI cache (Close + Volume)
  2. Yahoo Finance yfinance — currently returning 404 for .NR suffix (dead source)

Usage:
    python download_history.py              # export DB log for all tickers
    python download_history.py SCOM KCB    # specific tickers only
    python download_history.py --refresh   # alias for above (same behaviour)
    python download_history.py --status    # show how many DB rows per ticker

The bot's prewarm_cache_job writes one row/ticker/day to StockPriceLog every 4 min.
Run this script periodically (or after accumulating enough data) to regenerate CSVs.
"""

import os
import sys
import logging
import time
import pandas as pd

try:
    import yfinance as yf
    _yf_available = True
except ImportError:
    _yf_available = False

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

HISTORY_DIR = os.path.join(os.path.dirname(__file__), "data", "history")

# All NSE tickers confirmed on Yahoo Finance with .NR suffix
COVERED_TICKERS: list[str] = sorted([
    "SCOM", "KCB", "EQTY", "ABSA", "NCBA", "COOP", "SCBK", "DTK",
    "KPLC", "KEGN", "TOTL", "UMME",
    "EABL", "BAT", "CARB", "BOC",
    "JUB", "CIC", "BRIT", "KNRE", "SLAM",
    "BAMB", "CABL", "ARM",
    "NSE",
])

PERIOD_FULL    = "2y"   # initial bulk download
PERIOD_REFRESH = "3mo"  # incremental update window (catches any missed days)
DELAY_BETWEEN  = 1.5    # seconds between API calls — be polite to Yahoo


def csv_path(ticker: str) -> str:
    return os.path.join(HISTORY_DIR, f"{ticker}.csv")


def from_db(ticker: str) -> pd.DataFrame | None:
    """
    Read price history from StockPriceLog table.
    Returns DataFrame indexed by Date with columns: Close, Volume.
    Returns None if the DB is not reachable or has no rows for this ticker.
    """
    try:
        import os
        db_url = os.environ.get("DATABASE_URL", "sqlite:///portfolio.db")
        if db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
        from sqlalchemy import create_engine, text
        eng = create_engine(db_url, pool_pre_ping=True)
        with eng.connect() as conn:
            result = conn.execute(
                text("SELECT trade_date, close, volume, change, change_pct "
                     "FROM stock_price_log WHERE ticker = :t ORDER BY trade_date"),
                {"t": ticker.upper()}
            )
            rows = result.fetchall()
        if not rows:
            return None
        df = pd.DataFrame(rows, columns=["Date", "Close", "Volume", "Change", "ChangePct"])
        df["Date"] = pd.to_datetime(df["Date"])
        df.set_index("Date", inplace=True)
        df = df.round(4)
        return df
    except Exception as exc:
        logger.warning(f"{ticker}: DB read failed — {exc}")
        return None


def download_ticker_yf(ticker: str, period: str = PERIOD_FULL) -> pd.DataFrame | None:
    """Try Yahoo Finance. Currently returns 404 for NSE Kenya (.NR). Kept for future."""
    if not _yf_available:
        return None
    symbol = f"{ticker}.NR"
    try:
        df = yf.download(symbol, period=period, interval="1d",
                         auto_adjust=True, progress=False, timeout=20)
    except Exception as exc:
        logger.debug(f"{ticker}: yfinance failed — {exc}")
        return None
    if df is None or df.empty:
        return None
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[0] for col in df.columns]
    df.index.name = "Date"
    df = df[["Open", "High", "Low", "Close", "Volume"]].dropna().round(4)
    return df


def download_ticker(ticker: str, period: str = PERIOD_FULL) -> pd.DataFrame | None:
    """
    Get historical data: DB log first, Yahoo Finance fallback.
    Returns DataFrame with at least Date index + Close column.
    """
    df = from_db(ticker)
    if df is not None:
        logger.info(f"  DB  {ticker}: {len(df)} rows from StockPriceLog")
        return df
    df = download_ticker_yf(ticker, period=period)
    if df is not None:
        logger.info(f"  YF  {ticker}: {len(df)} rows from Yahoo Finance")
        return df
    return None


def save_ticker(ticker: str, df: pd.DataFrame, refresh: bool = False) -> int:
    """
    Write DataFrame to CSV. In refresh mode, merge with existing data
    so we only append genuinely new rows without duplicating.

    Returns number of rows written.
    """
    os.makedirs(HISTORY_DIR, exist_ok=True)
    path = csv_path(ticker)

    if refresh and os.path.exists(path):
        existing = pd.read_csv(path, index_col="Date", parse_dates=True)
        combined = pd.concat([existing, df])
        combined = combined[~combined.index.duplicated(keep="last")]
        combined.sort_index(inplace=True)
        combined.to_csv(path)
        rows = len(combined)
    else:
        df.sort_index(inplace=True)
        df.to_csv(path)
        rows = len(df)

    return rows


def run(tickers: list[str], refresh: bool = False) -> dict[str, int]:
    """
    Download and save history for the given tickers.
    Returns {ticker: row_count} for successfully saved tickers.
    """
    period = PERIOD_REFRESH if refresh else PERIOD_FULL
    results: dict[str, int] = {}

    logger.info(f"Downloading {len(tickers)} tickers  (period={period}, refresh={refresh})")
    for i, ticker in enumerate(tickers, 1):
        logger.info(f"[{i}/{len(tickers)}] {ticker} ...")
        df = download_ticker(ticker, period=period)
        if df is not None:
            rows = save_ticker(ticker, df, refresh=refresh)
            results[ticker] = rows
            logger.info(f"  ✓  {ticker}: {rows} rows → {csv_path(ticker)}")
        else:
            logger.warning(f"  ✗  {ticker}: skipped (no data)")
        if i < len(tickers):
            time.sleep(DELAY_BETWEEN)

    return results


def show_status() -> None:
    """Print how many DB rows exist per ticker."""
    try:
        import os
        db_url = os.environ.get("DATABASE_URL", "sqlite:///portfolio.db")
        if db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
        from sqlalchemy import create_engine, text
        eng = create_engine(db_url, pool_pre_ping=True)
        with eng.connect() as conn:
            rows = conn.execute(text(
                "SELECT ticker, COUNT(*) as cnt, MIN(trade_date) as first_date, MAX(trade_date) as last_date "
                "FROM stock_price_log GROUP BY ticker ORDER BY ticker"
            )).fetchall()
        if not rows:
            print("No price data in DB yet. The bot needs to run for at least one trading day.")
            return
        print(f"\n{'Ticker':<10} {'Rows':>6}  {'First':>12}  {'Last':>12}")
        print("-" * 46)
        for ticker, cnt, first, last in rows:
            print(f"{ticker:<10} {cnt:>6}  {str(first):>12}  {str(last):>12}")
        total = sum(r[1] for r in rows)
        print(f"\nTotal: {total} rows across {len(rows)} tickers")
    except Exception as exc:
        print(f"DB status failed: {exc}")


def main() -> None:
    args = sys.argv[1:]

    if "--status" in args:
        show_status()
        return

    refresh = "--refresh" in args
    args = [a for a in args if not a.startswith("--")]

    tickers = [a.upper() for a in args] if args else COVERED_TICKERS

    results = run(tickers, refresh=refresh)

    print(f"\n{'=' * 50}")
    print(f"Done: {len(results)}/{len(tickers)} tickers saved")
    for ticker, rows in sorted(results.items()):
        print(f"  {ticker:<8} {rows:>4} rows")

    missing = [t for t in tickers if t not in results]
    if missing:
        print(f"\nNo data found for: {', '.join(missing)}")
        print("These will use GBM simulation in /predict. Data will accumulate via the bot's daily price log.")


if __name__ == "__main__":
    main()
