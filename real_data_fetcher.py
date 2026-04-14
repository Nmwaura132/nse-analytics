"""
Real Data Fetcher — Yahoo Finance (yfinance) for NSE stocks.

Yahoo Finance uses the `.NR` suffix for Nairobi Securities Exchange tickers,
e.g. SCOM.NR, KCB.NR, EQTY.NR.

This module is the first data priority in MLPredictor.get_data():
  1. Real CSV  →  2. yfinance (this module)  →  3. GBM simulation  →  4. Emergency

Design decisions:
- Returns None (not empty DataFrame) when a ticker is not covered so the
  caller can cleanly distinguish "no data source" from "empty fetch".
- Caches the last successful fetch per ticker for CACHE_TTL seconds to avoid
  hammering Yahoo on every /forecast command.
- `get_current_price()` uses yf.fast_info which is a lightweight ticker ping
  (~1 HTTP request vs the heavier yf.download).
"""

from __future__ import annotations

import logging
import time
from typing import Optional

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# NSE tickers confirmed available on Yahoo Finance (TICKER.NR)
# ---------------------------------------------------------------------------
COVERED_TICKERS: frozenset[str] = frozenset({
    "SCOM", "KCB", "EQTY", "ABSA", "NCBA", "COOP", "SCBK", "DTK",
    "KPLC", "KEGN", "TOTL", "UMME",
    "EABL", "BAT", "CARB", "BOC",
    "JUB", "CIC", "BRIT", "KNRE", "SLAM",
    "BAMB", "CABL", "ARM",
    "NSE",  # NSE itself
})

CACHE_TTL = 300  # 5 minutes — aligns with bot cache interval


class YFinanceNSEFetcher:
    """
    Fetches real OHLCV history and live prices for NSE stocks via Yahoo Finance.
    """

    NSE_SUFFIX = ".NR"

    def __init__(self) -> None:
        # ticker -> {"df": pd.DataFrame, "ts": float, "price": float}
        self._cache: dict[str, dict] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def is_covered(self, ticker: str) -> bool:
        """Return True if Yahoo Finance covers this ticker."""
        return ticker.upper() in COVERED_TICKERS

    def get_history(
        self,
        ticker: str,
        period: str = "6mo",
        interval: str = "1d",
    ) -> Optional[pd.DataFrame]:
        """
        Fetch OHLCV history for *ticker*.

        Args:
            ticker:   NSE ticker symbol (without suffix), e.g. "SCOM".
            period:   yfinance period string — "1mo", "3mo", "6mo", "1y".
            interval: yfinance interval — "1d" (daily) or "1wk".

        Returns:
            DataFrame with columns [Open, High, Low, Close, Volume] indexed by Date,
            or None if the ticker is not covered / the download fails.
        """
        ticker = ticker.upper()

        # Serve from cache if fresh
        cached = self._cache.get(ticker)
        if cached and (time.time() - cached["ts"]) < CACHE_TTL:
            return cached.get("df")

        if not self.is_covered(ticker):
            logger.debug(f"yfinance: {ticker} not in covered set — skipping")
            return None

        yf_symbol = f"{ticker}{self.NSE_SUFFIX}"
        try:
            df = yf.download(
                yf_symbol,
                period=period,
                interval=interval,
                auto_adjust=True,
                progress=False,
                timeout=15,
            )
        except Exception as exc:
            logger.warning(f"yfinance download failed for {yf_symbol}: {exc}")
            return None

        if df is None or df.empty:
            logger.warning(f"yfinance returned empty DataFrame for {yf_symbol}")
            return None

        # Normalise column names — yfinance returns MultiIndex when downloading
        # a single ticker; flatten to simple column names.
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col[0] for col in df.columns]

        df.index.name = "Date"
        df = df[["Open", "High", "Low", "Close", "Volume"]].dropna()

        self._cache[ticker] = {"df": df, "ts": time.time()}
        logger.info(f"yfinance: loaded {len(df)} rows for {yf_symbol}")
        return df

    def get_current_price(self, ticker: str) -> Optional[float]:
        """
        Return the latest price for *ticker* using yfinance fast_info.

        Returns None if the ticker is not covered or the lookup fails.
        This is cheaper than re-downloading full OHLCV history.
        """
        ticker = ticker.upper()
        if not self.is_covered(ticker):
            return None

        try:
            fast_info = yf.Ticker(f"{ticker}{self.NSE_SUFFIX}").fast_info
            price = fast_info.get("last_price") or fast_info.get("regularMarketPrice")
            return float(price) if price else None
        except Exception as exc:
            logger.warning(f"yfinance price lookup failed for {ticker}: {exc}")
            return None

    def get_batch_prices(self, tickers: list[str]) -> dict[str, float]:
        """
        Bulk-download latest prices for multiple tickers in a single HTTP call.
        Returns {ticker: price} for successfully fetched tickers only.
        """
        covered = [t.upper() for t in tickers if self.is_covered(t)]
        if not covered:
            return {}

        symbols = " ".join(f"{t}{self.NSE_SUFFIX}" for t in covered)
        try:
            data = yf.download(symbols, period="1d", auto_adjust=True, progress=False, timeout=20)
            if data is None or data.empty:
                return {}

            # ('Close', 'SCOM.NR') style MultiIndex → flatten
            if isinstance(data.columns, pd.MultiIndex):
                close = data["Close"]
                prices = {}
                for col in close.columns:
                    raw_ticker = col.replace(self.NSE_SUFFIX, "").upper()
                    last = close[col].dropna()
                    if not last.empty:
                        prices[raw_ticker] = float(last.iloc[-1])
                return prices
        except Exception as exc:
            logger.warning(f"yfinance batch price fetch failed: {exc}")
        return {}
