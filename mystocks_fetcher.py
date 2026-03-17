"""
MyStocks Data Fetcher
Authenticated scraper for live.mystocks.co.ke
Provides more accurate data including dividends and corporate actions.
"""
import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import re
import json
from datetime import datetime
from typing import Optional

class MyStocksFetcher:
    BASE_URL = "https://live.mystocks.co.ke"
    LOGIN_URL = "https://live.mystocks.co.ke/login/"
    
    def __init__(self, username: str = None, password: str = None):
        """
        Initialize with credentials from params or environment.
        Set MYSTOCKS_USERNAME and MYSTOCKS_PASSWORD in .env
        """
        self.username = username or os.getenv('MYSTOCKS_USERNAME')
        self.password = password or os.getenv('MYSTOCKS_PASSWORD')
        
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        })
        self.logged_in = False
    
    def login(self) -> bool:
        """Authenticate with mystocks.co.ke"""
        if not self.username or not self.password:
            print("Warning: No mystocks credentials provided. Using public data only.")
            return False
        
        try:
            # Get login page for CSRF token
            login_page = self.session.get(self.LOGIN_URL)
            soup = BeautifulSoup(login_page.text, 'html.parser')
            
            # Find hidden fields
            action_input = soup.find('input', {'name': 'action'})
            pg_input = soup.find('input', {'name': 'pg'})
            
            # Submit login form - using correct field names from the form
            login_data = {
                'email': self.username,
                'passwd': self.password,
                'action': action_input['value'] if action_input else '',
                'pg': pg_input['value'] if pg_input else '',
                'login': 'Sign In'  # Submit button
            }
            
            response = self.session.post(self.LOGIN_URL, data=login_data, allow_redirects=True)
            
            # Check if login succeeded by looking for logout link or user menu
            if 'logout' in response.text.lower() or 'my portfolio' in response.text.lower() or 'sign out' in response.text.lower():
                self.logged_in = True
                print("Successfully logged in to mystocks.co.ke")
                return True
            else:
                print("Login may have failed - checking for error messages...")
                if 'invalid' in response.text.lower() or 'incorrect' in response.text.lower():
                    print("Invalid credentials")
                return False
                
        except Exception as e:
            print(f"Login error: {e}")
            return False
    
    def get_stock_quote(self, ticker: str) -> dict:
        """
        Fetch real-time quote for a stock.
        Returns: price, change, volume, etc.
        """
        url = f"{self.BASE_URL}/stock={ticker}"
        result = {
            'ticker': ticker.upper(),
            'price': None,
            'change': None,
            'change_pct': None,
            'volume': None,
            'bid': None,
            'ask': None,
            'high': None,
            'low': None,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            response = self.session.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Parse the page for price data
            # Looking for common patterns in stock quote pages
            text = soup.get_text(separator='|')
            
            # Try to extract price patterns like "31.90" or "KES 31.90"
            price_patterns = [
                r'Current Price[:\s|]+(\d+\.?\d*)',
                r'Last Traded[:\s|]+(\d+\.?\d*)',
                r'Close[:\s|]+(\d+\.?\d*)',
                r'KES\s*(\d+\.?\d*)',
            ]
            
            for pattern in price_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    result['price'] = float(match.group(1))
                    break
            
            # Extract change
            change_match = re.search(r'Change[:\s|]+([+-]?\d+\.?\d*)', text, re.IGNORECASE)
            if change_match:
                result['change'] = float(change_match.group(1))
            
            # Extract volume
            volume_match = re.search(r'Volume[:\s|]+([\d,]+)', text, re.IGNORECASE)
            if volume_match:
                result['volume'] = int(volume_match.group(1).replace(',', ''))
            
            return result
            
        except Exception as e:
            print(f"Error fetching quote for {ticker}: {e}")
            return result
    
    def get_fundamentals(self, ticker: str) -> dict:
        """
        Fetch fundamental data: EPS, P/E, DPS, Dividend Yield, etc.
        """
        url = f"{self.BASE_URL}/stock={ticker}?fundamentals"
        result = {
            'ticker': ticker.upper(),
            'eps': None,
            'pe_ratio': None,
            'dps': None,
            'dividend_yield': None,
            'book_value': None,
            'market_cap': None,
            'shares_outstanding': None
        }
        
        try:
            response = self.session.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            text = soup.get_text(separator='|')
            
            # Extract fundamental metrics
            patterns = {
                'eps': r'(?:EPS|Earnings Per Share)[:\s|]*([\d.]+)',
                'pe_ratio': r'(?:P/E|Price.?Earning|PE Ratio)[:\s|]*([\d.]+)',
                'dps': r'(?:DPS|Dividend Per Share)[:\s|]*([\d.]+)',
                'dividend_yield': r'(?:Dividend Yield)[:\s|]*([\d.]+)%?',
                'book_value': r'(?:Book Value)[:\s|]*([\d.]+)',
            }
            
            for key, pattern in patterns.items():
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    result[key] = float(match.group(1))
            
            return result
            
        except Exception as e:
            print(f"Error fetching fundamentals for {ticker}: {e}")
            return result
    
    def get_corporate_actions(self, ticker: str) -> list:
        """
        Fetch corporate actions: dividends, book closure dates, AGMs, etc.
        """
        url = f"{self.BASE_URL}/stock={ticker}?corporate_actions"
        actions = []
        
        try:
            response = self.session.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for tables with corporate action data
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        text = ' '.join(c.get_text(strip=True) for c in cells)
                        
                        # Check for dividend or book closure mentions
                        if any(kw in text.lower() for kw in ['dividend', 'book closure', 'agm', 'bonus']):
                            actions.append({
                                'ticker': ticker.upper(),
                                'description': text,
                                'raw_data': [c.get_text(strip=True) for c in cells]
                            })
            
            return actions
            
        except Exception as e:
            print(f"Error fetching corporate actions for {ticker}: {e}")
            return actions
    
    def get_historical_prices(self, ticker: str, days: int = 30) -> pd.DataFrame:
        """
        Fetch historical price data.
        """
        url = f"{self.BASE_URL}/stock={ticker}?historical"
        
        try:
            response = self.session.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try to find price table
            tables = soup.find_all('table')
            
            for table in tables:
                headers = [th.get_text(strip=True).lower() for th in table.find_all('th')]
                if any('date' in h for h in headers) and any('close' in h or 'price' in h for h in headers):
                    # Found the right table
                    rows = []
                    for tr in table.find_all('tr')[1:]:  # Skip header
                        cells = [td.get_text(strip=True) for td in tr.find_all('td')]
                        if len(cells) >= 2:
                            rows.append(cells)
                    
                    if rows:
                        df = pd.DataFrame(rows)
                        # Try to assign column names based on header count
                        if len(df.columns) >= 5:
                            df.columns = ['Date', 'Open', 'High', 'Low', 'Close'][:len(df.columns)]
                        elif len(df.columns) >= 2:
                            df.columns = ['Date', 'Close'] + [f'Col{i}' for i in range(len(df.columns)-2)]
                        
                        return df.head(days)
            
            return pd.DataFrame()
            
        except Exception as e:
            print(f"Error fetching historical prices for {ticker}: {e}")
            return pd.DataFrame()
    
    def get_market_summary(self) -> dict:
        """
        Fetch overall market summary: indices, top gainers/losers.
        """
        url = f"{self.BASE_URL}/"
        summary = {
            'nse_20': None,
            'nse_25': None,
            'nasi': None,
            'gainers': [],
            'losers': []
        }
        
        try:
            response = self.session.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            text = soup.get_text(separator='|')
            
            # Extract index values
            nse20_match = re.search(r'NSE.?20[:\s|]*([\d,.]+)', text, re.IGNORECASE)
            if nse20_match:
                summary['nse_20'] = float(nse20_match.group(1).replace(',', ''))
            
            nasi_match = re.search(r'NASI[:\s|]*([\d,.]+)', text, re.IGNORECASE)
            if nasi_match:
                summary['nasi'] = float(nasi_match.group(1).replace(',', ''))
            
            return summary
            
        except Exception as e:
            print(f"Error fetching market summary: {e}")
            return summary


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    fetcher = MyStocksFetcher()
    
    # Try to login
    if fetcher.login():
        print("\n--- Testing with authenticated session ---")
    else:
        print("\n--- Testing without authentication (public data only) ---")
    
    # Test quote
    print("\nFetching SCOM quote...")
    quote = fetcher.get_stock_quote("SCOM")
    print(f"Quote: {quote}")
    
    # Test fundamentals
    print("\nFetching SCOM fundamentals...")
    fundamentals = fetcher.get_fundamentals("SCOM")
    print(f"Fundamentals: {fundamentals}")
    
    # Test corporate actions
    print("\nFetching SCOM corporate actions...")
    actions = fetcher.get_corporate_actions("SCOM")
    print(f"Corporate Actions: {actions}")
