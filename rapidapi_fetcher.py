"""
RapidAPI NSE Data Fetcher
Fast, reliable real-time data for all NSE Kenya stocks.
"""
import requests
import os
import re
from datetime import datetime
from typing import Optional, List
import pandas as pd

class RapidAPIFetcher:
    BASE_URL = "https://nairobi-stock-exchange-nse.p.rapidapi.com"
    
    def __init__(self, api_key: str = None):
        """
        Initialize with API key from param or environment.
        Set RAPIDAPI_KEY in .env
        """
        self.api_key = api_key or os.getenv('RAPIDAPI_KEY')
        
        if not self.api_key:
            raise ValueError("RAPIDAPI_KEY is required. Set it in .env or pass to constructor.")
        
        self.headers = {
            "x-rapidapi-host": "nairobi-stock-exchange-nse.p.rapidapi.com",
            "x-rapidapi-key": self.api_key
        }
    
    def _parse_numeric(self, value: str) -> Optional[float]:
        """Parse numeric strings with commas."""
        if not value:
            return None
        try:
            # Remove commas and percentage signs
            clean = value.replace(',', '').replace('%', '').strip()
            # Handle +/- signs
            if clean.startswith('+'):
                clean = clean[1:]
            return float(clean)
        except (ValueError, TypeError):
            return None
    
    def _parse_change(self, change_str: str) -> dict:
        """Parse change string like '+0.05' or '+0.05 (+0.16%)'"""
        result = {'change': None, 'change_pct': None}
        if not change_str:
            return result
        
        # Extract numeric change
        change_match = re.match(r'([+-]?\d+\.?\d*)', change_str)
        if change_match:
            result['change'] = float(change_match.group(1))
        
        # Extract percentage if present
        pct_match = re.search(r'\(([+-]?\d+\.?\d*)%\)', change_str)
        if pct_match:
            result['change_pct'] = float(pct_match.group(1))
        
        return result
    
    def get_all_stocks(self) -> List[dict]:
        """
        Fetch all NSE stocks with current prices.
        Returns list of stock dicts with: ticker, name, price, volume, change
        """
        try:
            response = requests.get(
                f"{self.BASE_URL}/stocks",
                headers=self.headers,
                timeout=60
            )
            response.raise_for_status()
            data = response.json()
            
            if not data.get('success'):
                print(f"API returned error: {data}")
                return []
            
            stocks = []
            for item in data.get('data', []):
                change_data = self._parse_change(item.get('change', ''))
                stocks.append({
                    'ticker': item.get('ticker'),
                    'name': item.get('name'),
                    'price': self._parse_numeric(item.get('price')),
                    'volume': self._parse_numeric(item.get('volume')),
                    'change': change_data['change'],
                    'change_pct': change_data['change_pct'],
                    'timestamp': data.get('meta', {}).get('lastUpdated')
                })
            
            return stocks
            
        except Exception as e:
            print(f"Error fetching stocks: {e}")
            return []
    
    def get_stock(self, ticker_or_name: str) -> Optional[dict]:
        """
        Fetch a specific stock by ticker or company name.
        """
        try:
            response = requests.get(
                f"{self.BASE_URL}/stocks",
                headers=self.headers,
                params={"search": ticker_or_name},
                timeout=60
            )
            response.raise_for_status()
            data = response.json()
            
            if not data.get('success') or not data.get('data'):
                return None
            
            item = data['data'][0]
            change_data = self._parse_change(item.get('change', ''))
            
            return {
                'ticker': item.get('ticker'),
                'name': item.get('name'),
                'price': self._parse_numeric(item.get('price')),
                'volume': self._parse_numeric(item.get('volume')),
                'change': change_data['change'],
                'change_pct': change_data['change_pct'],
                'timestamp': data.get('meta', {}).get('lastUpdated')
            }
            
        except Exception as e:
            print(f"Error fetching stock {ticker_or_name}: {e}")
            return None
    
    def get_gainers(self, limit: int = 5) -> List[dict]:
        """Get top gainers by change amount."""
        stocks = self.get_all_stocks()
        # Filter stocks with positive change
        gainers = [s for s in stocks if s['change'] and s['change'] > 0]
        # Sort by change descending
        gainers.sort(key=lambda x: x['change'], reverse=True)
        return gainers[:limit]
    
    def get_losers(self, limit: int = 5) -> List[dict]:
        """Get top losers by change amount."""
        stocks = self.get_all_stocks()
        # Filter stocks with negative change
        losers = [s for s in stocks if s['change'] and s['change'] < 0]
        # Sort by change ascending (most negative first)
        losers.sort(key=lambda x: x['change'])
        return losers[:limit]
    
    def get_most_active(self, limit: int = 5) -> List[dict]:
        """Get most active stocks by volume."""
        stocks = self.get_all_stocks()
        # Filter stocks with volume
        active = [s for s in stocks if s['volume'] and s['volume'] > 0]
        # Sort by volume descending
        active.sort(key=lambda x: x['volume'], reverse=True)
        return active[:limit]
    
    def to_dataframe(self, stocks: List[dict] = None) -> pd.DataFrame:
        """Convert stock list to pandas DataFrame."""
        if stocks is None:
            stocks = self.get_all_stocks()
        return pd.DataFrame(stocks)


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    fetcher = RapidAPIFetcher()
    
    print("=== Fetching all stocks ===")
    stocks = fetcher.get_all_stocks()
    if stocks:
        print(f"Raw Keys available: {stocks[0].keys()}")
    print(f"Total stocks: {len(stocks)}")
    
    print("\n=== Top 5 Gainers ===")
    for s in fetcher.get_gainers():
        print(f"  {s['ticker']}: {s['price']} ({s['change']:+.2f})")
    
    print("\n=== Top 5 Losers ===")
    for s in fetcher.get_losers():
        print(f"  {s['ticker']}: {s['price']} ({s['change']:+.2f})")
    
    print("\n=== Most Active ===")
    for s in fetcher.get_most_active():
        print(f"  {s['ticker']}: Volume {s['volume']:,.0f}")
    
    print("\n=== Specific Stock (SCOM) ===")
    scom = fetcher.get_stock("SCOM")
    print(f"  {scom}")
