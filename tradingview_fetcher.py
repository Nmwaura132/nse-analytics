"""
TradingView NSE Data Fetcher
Auth-free, fast, and reliable real-time and fundamental data for NSE Kenya stocks.
Uses TradingView's lightweight scanner endpoint.
"""
import requests
import json
import pandas as pd
from datetime import datetime
from typing import Optional, List

class TradingViewFetcher:
    SCANNER_URL = "https://scanner.tradingview.com/kenya/scan"
    
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        # Define the exact columns we want backwards from TradingView
        # Mapping: name, close, change%, volume, marketcap, pe, div_yield, eps, pb
        self.tv_columns = [
            'name', 
            'close', 
            'change', 
            'volume', 
            'market_cap_basic', 
            'price_earnings_ttm', 
            'dividend_yield_recent', 
            'earnings_per_share_basic_ttm', 
            'price_book_ratio'
        ]

    def _fetch_scan(self, payload: dict) -> List[dict]:
        """Base method to query the TradingView scanner."""
        try:
            response = requests.post(self.SCANNER_URL, json=payload, headers=self.headers, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            if 'data' not in data:
                return []
                
            stocks = []
            now = datetime.now().isoformat()
            
            for item in data['data']:
                # The 'd' array contains the requested columns in exact order
                d = item['d']
                ticker = d[0]
                
                # Extract numeric change from percentage change
                price = d[1]
                change_pct = d[2]
                change = None
                if price is not None and change_pct is not None:
                    # Calculate KES absolute change from percentage
                    change = price - (price / (1 + (change_pct / 100)))
                    
                stocks.append({
                    'ticker': ticker,
                    'name': ticker,  # Trading View Scanner 'name' is just ticker. Use ticker for name
                    'price': price,
                    'change': round(change, 4) if change is not None else 0.0,
                    'change_pct': round(change_pct, 4) if change_pct is not None else 0.0,
                    'volume': d[3] if d[3] is not None else 0,
                    'market_cap': d[4],
                    'pe_ratio': round(d[5], 2) if d[5] is not None else None,
                    'dividend_yield': round(d[6], 2) if d[6] is not None else None,
                    'eps': round(d[7], 2) if d[7] is not None else None,
                    'pb_ratio': round(d[8], 2) if d[8] is not None else None,
                    'timestamp': now
                })
                
            return stocks
            
        except Exception as e:
            print(f"TradingView Fetch Error: {e}")
            return []

    def get_all_stocks(self) -> List[dict]:
        """
        Fetch all NSE stocks with current prices.
        """
        payload = {
            "filter": [{"left": "type", "operation": "equal", "right": "stock"}],
            "options": {"lang": "en"},
            "markets": ["kenya"],
            "symbols": {"query": {"types": []}, "tickers": []},
            "columns": self.tv_columns,
            "sort": {"sortBy": "market_cap_basic", "sortOrder": "desc"},
            "range": [0, 100]  # NSE has ~65 stocks
        }
        return self._fetch_scan(payload)

    def get_stock(self, ticker: str) -> Optional[dict]:
        """
        Fetch a specific stock by ticker.
        """
        # Clean ticker
        ticker = ticker.upper().strip()
        if not ticker.startswith("NSEKE:"):
            # Try plain ticker, TradingView scanner for specific needs the exchange prefix
            # Alternatively, if we just use ticker list filter:
            ticker = f"NSEKE:{ticker}"
            
        payload = {
            "symbols": {"tickers": [ticker]},
            "columns": self.tv_columns
        }
        results = self._fetch_scan(payload)
        return results[0] if results else None
        
    def get_fundamentals(self, ticker: str) -> dict:
        """
        Fetch fundamental data (matches mystocks_fetcher signature)
        """
        stock = self.get_stock(ticker)
        if not stock:
             return {}
        
        return {
            'ticker': stock['ticker'],
            'eps': stock['eps'],
            'pe_ratio': stock['pe_ratio'],
            'dividend_yield': stock['dividend_yield'],
            'book_value': None, # We have Price/Book instead
            'market_cap': stock['market_cap']
        }

    def get_gainers(self, limit: int = 5) -> List[dict]:
        """Get top gainers by change %."""
        stocks = self.get_all_stocks()
        gainers = [s for s in stocks if s['change_pct'] and s['change_pct'] > 0]
        gainers.sort(key=lambda x: x['change_pct'], reverse=True)
        return gainers[:limit]
    
    def get_losers(self, limit: int = 5) -> List[dict]:
        """Get top losers by change %."""
        stocks = self.get_all_stocks()
        losers = [s for s in stocks if s['change_pct'] and s['change_pct'] < 0]
        losers.sort(key=lambda x: x['change_pct'])
        return losers[:limit]
    
    def get_most_active(self, limit: int = 5) -> List[dict]:
        """Get most active stocks by volume."""
        stocks = self.get_all_stocks()
        active = [s for s in stocks if s['volume'] and s['volume'] > 0]
        active.sort(key=lambda x: x['volume'], reverse=True)
        return active[:limit]
    
    def to_dataframe(self, stocks: List[dict] = None) -> pd.DataFrame:
        """Convert stock list to pandas DataFrame."""
        if stocks is None:
            stocks = self.get_all_stocks()
        return pd.DataFrame(stocks)


if __name__ == "__main__":
    fetcher = TradingViewFetcher()
    
    print("=== Fetching all stocks ===")
    stocks = fetcher.get_all_stocks()
    print(f"Total stocks: {len(stocks)}")
    if stocks:
        print(f"Sample (KPLC): {[s for s in stocks if s['ticker'] == 'KPLC']}")
        
    print("\n=== Fetching Specific Stock (SCOM) ===")
    scom = fetcher.get_stock("SCOM")
    for k, v in scom.items():
         print(f"{k}: {v}")
