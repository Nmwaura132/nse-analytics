"""
NSE Historical Price Backfill
Downloads up to 5 years of daily OHLCV from stooq.com and upserts into:
  - stock_price_log  (read by ml_predictor.py via download_history.py)
  - price_history    (read by Django API + bot analytics)

SETUP (one time only):
  Stooq.com now requires a free API key obtained via CAPTCHA:
  1. Open https://stooq.com/q/d/?s=SCOM.KE&get_apikey in your browser
  2. Solve the CAPTCHA
  3. Copy the <apikey> value from the download URL shown
  4. Pass it as: python backfill_nse_history.py --stooq-key=YOUR_KEY
     Or set:   export STOOQ_API_KEY=YOUR_KEY

Run inside the nse-bot container:
    docker cp backfill_nse_history.py $BOT:/app/
    docker exec -e STOOQ_API_KEY=YOUR_KEY $BOT python backfill_nse_history.py
    docker exec $BOT python download_history.py --refresh   # regenerate CSVs
    docker exec $BOT python download_history.py --status    # verify counts

Or locally against the production DB:
    STOOQ_API_KEY=YOUR_KEY DATABASE_URL=postgresql://nse_user:PASS@37.221.93.219:5432/nse_db python backfill_nse_history.py
"""

import os
import sys
import time
import logging
import io

import pandas as pd
import requests
from sqlalchemy import create_engine, text

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# NSE ticker → stooq.com symbol
STOOQ_MAP: dict[str, str] = {
    "SCOM":  "SCOM.KE",
    "KCB":   "KCB.KE",
    "EQTY":  "EQTY.KE",
    "ABSA":  "ABSA.KE",
    "NCBA":  "NCBA.KE",
    "COOP":  "COOP.KE",
    "SCBK":  "SCBK.KE",
    "DTK":   "DTK.KE",
    "KPLC":  "KPLC.KE",
    "KEGN":  "KEGN.KE",
    "TOTL":  "TOTL.KE",
    "UMME":  "UMME.KE",
    "EABL":  "EABL.KE",
    "BAT":   "BAT.KE",
    "CARB":  "CARB.KE",
    "BOC":   "BOC.KE",
    "JUB":   "JUB.KE",
    "CIC":   "CIC.KE",
    "BRIT":  "BRIT.KE",
    "KNRE":  "KNRE.KE",
    "SLAM":  "SLAM.KE",
    "BAMB":  "BAMB.KE",
    "CABL":  "CABL.KE",
    "ARM":   "ARM.KE",
    "NSE":   "NSE.KE",
}

STOOQ_BASE = "https://stooq.com/q/d/l/?s={symbol}&i=d"
DELAY_SEC = 2.0   # seconds between stooq requests
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; NSE-backfill/1.0; +https://nseanalytics.co.ke)",
    "Accept": "text/csv,text/plain,*/*",
}


def get_stooq_key() -> str:
    """Get stooq API key from env or CLI args."""
    # Check CLI arg: --stooq-key=KEY
    for arg in sys.argv[1:]:
        if arg.startswith('--stooq-key='):
            return arg.split('=', 1)[1].strip()
    return os.environ.get("STOOQ_API_KEY", "")


def get_engine():
    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url:
        logger.error("DATABASE_URL not set")
        sys.exit(1)
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return create_engine(db_url, pool_pre_ping=True)


def fetch_stooq(stooq_sym: str, api_key: str = "") -> pd.DataFrame | None:
    url = STOOQ_BASE.format(symbol=stooq_sym)
    if api_key:
        url += f"&k={api_key}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        if len(resp.content) < 50:
            logger.warning(f"  {stooq_sym}: empty response (ticker may not exist on stooq)")
            return None
        df = pd.read_csv(io.StringIO(resp.text), parse_dates=["Date"])
        if df.empty or "Close" not in df.columns:
            logger.warning(f"  {stooq_sym}: no usable data")
            return None
        df = df.sort_values("Date").reset_index(drop=True)
        df = df[["Date", "Open", "High", "Low", "Close", "Volume"]].dropna(subset=["Close"])
        # Calculate daily change from Close prices
        df["change"] = (df["Close"] - df["Close"].shift(1)).round(4).fillna(0)
        df["change_pct"] = (df["change"] / df["Close"].shift(1) * 100).round(4).fillna(0)
        logger.info(f"  {stooq_sym}: fetched {len(df)} rows  "
                    f"({df['Date'].min().date()} → {df['Date'].max().date()})")
        return df
    except requests.HTTPError as e:
        logger.warning(f"  {stooq_sym}: HTTP {e.response.status_code}")
        return None
    except Exception as e:
        logger.warning(f"  {stooq_sym}: {e}")
        return None


def upsert_stock_price_log(engine, ticker: str, df: pd.DataFrame) -> int:
    inserted = 0
    with engine.begin() as conn:
        for _, row in df.iterrows():
            result = conn.execute(text("""
                INSERT INTO stock_price_log
                    (ticker, trade_date, close, volume, change, change_pct)
                VALUES
                    (:ticker, :trade_date, :close, :volume, :change, :change_pct)
                ON CONFLICT (ticker, trade_date) DO NOTHING
            """), {
                "ticker":      ticker,
                "trade_date":  row["Date"].date(),
                "close":       float(row["Close"]),
                "volume":      float(row["Volume"]) if pd.notna(row["Volume"]) else 0.0,
                "change":      float(row["change"]),
                "change_pct":  float(row["change_pct"]),
            })
            inserted += result.rowcount
    return inserted


def upsert_price_history(engine, ticker: str, df: pd.DataFrame) -> int:
    inserted = 0
    with engine.begin() as conn:
        for _, row in df.iterrows():
            result = conn.execute(text("""
                INSERT INTO price_history
                    (ticker, date, close, volume, change_abs, change_pct, source)
                VALUES
                    (:ticker, :date, :close, :volume, :change_abs, :change_pct, 'backfill')
                ON CONFLICT (ticker, date) DO NOTHING
            """), {
                "ticker":     ticker,
                "date":       row["Date"].date(),
                "close":      float(row["Close"]),
                "volume":     float(row["Volume"]) if pd.notna(row["Volume"]) else 0.0,
                "change_abs": float(row["change"]),
                "change_pct": float(row["change_pct"]),
            })
            inserted += result.rowcount
    return inserted


def check_table_exists(engine, table_name: str) -> bool:
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
            "WHERE table_name = :t)"
        ), {"t": table_name})
        return result.scalar()


def main():
    tickers_arg = [a.upper() for a in sys.argv[1:] if not a.startswith("--")]
    tickers = tickers_arg if tickers_arg else list(STOOQ_MAP.keys())
    api_key = get_stooq_key()

    if not api_key:
        print("\n⚠️  Stooq API key required (free):")
        print("  1. Open https://stooq.com/q/d/?s=SCOM.KE&get_apikey in your browser")
        print("  2. Solve the CAPTCHA")
        print("  3. Copy the <apikey> value from the download link shown")
        print("  4. Run:  python backfill_nse_history.py --stooq-key=YOUR_KEY")
        print("     Or:   STOOQ_API_KEY=YOUR_KEY python backfill_nse_history.py\n")
        sys.exit(1)

    engine = get_engine()

    # Verify tables exist
    for tbl in ("stock_price_log", "price_history"):
        if not check_table_exists(engine, tbl):
            logger.error(f"Table '{tbl}' does not exist — run Django migrations first")
            sys.exit(1)

    logger.info(f"Starting backfill for {len(tickers)} tickers (stooq key: {api_key[:6]}...)")
    summary: list[tuple[str, int, int]] = []

    for i, ticker in enumerate(tickers, 1):
        stooq_sym = STOOQ_MAP.get(ticker)
        if not stooq_sym:
            logger.warning(f"[{i}/{len(tickers)}] {ticker}: no stooq mapping, skipping")
            continue

        logger.info(f"[{i}/{len(tickers)}] {ticker} ({stooq_sym})")
        df = fetch_stooq(stooq_sym, api_key)

        if df is None or df.empty:
            summary.append((ticker, 0, 0))
        else:
            n1 = upsert_stock_price_log(engine, ticker, df)
            n2 = upsert_price_history(engine, ticker, df)
            summary.append((ticker, n1, n2))
            logger.info(f"    stock_price_log: +{n1} rows  |  price_history: +{n2} rows")

        if i < len(tickers):
            time.sleep(DELAY_SEC)

    print(f"\n{'=' * 60}")
    print(f"{'Ticker':<10} {'price_log':>10} {'price_hist':>12}")
    print(f"{'-' * 34}")
    for ticker, n1, n2 in summary:
        status = "✓" if n1 > 0 else "✗"
        print(f"  {status} {ticker:<8} {n1:>10,}  {n2:>10,}")
    total1 = sum(r[1] for r in summary)
    total2 = sum(r[2] for r in summary)
    print(f"\n  Total: {total1:,} rows → stock_price_log | {total2:,} rows → price_history")
    print(f"\nNext steps:")
    print(f"  python download_history.py --refresh  # generate CSVs for ML")
    print(f"  python download_history.py --status   # verify row counts")


if __name__ == "__main__":
    main()
