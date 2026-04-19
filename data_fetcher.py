import re
import requests
from bs4 import BeautifulSoup
import pandas as pd
import datetime
import time
import traceback

class NSEDataFetcher:
    BASE_URL = "https://afx.kwayisi.org/nse/"
    HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120"}

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)

    def get_all_stocks(self):
        """Scrape all NSE stocks with live prices from afx.kwayisi.org."""
        try:
            r = self.session.get(self.BASE_URL, timeout=20)
            r.raise_for_status()
            pattern = r'>([A-Z][A-Z0-9-]{1,7})</a><td>(?:<a[^>]+>[^<]+</a><td>)?([\d,]*)<td>([\d,\.]+)<td[^>]*>([+-][\d\.]+)<tr'
            stocks = []
            seen = set()
            for ticker, vol_str, price_str, change_str in re.findall(pattern, r.text):
                if ticker in seen:
                    continue
                seen.add(ticker)
                try:
                    price = float(price_str.replace(',', ''))
                    change = float(change_str)
                    prev = price - change
                    chg_pct = round((change / prev) * 100, 2) if prev else 0.0
                    stocks.append({
                        'ticker': ticker,
                        'name': ticker,
                        'price': price,
                        'volume': float(vol_str.replace(',', '')) if vol_str else 0,
                        'change': change,
                        'change_pct': chg_pct,
                        'timestamp': datetime.datetime.now().isoformat(),
                    })
                except Exception:
                    pass
            return stocks
        except Exception as e:
            print(f"AFX fetch error: {e}")
            return []

    def get_stock(self, ticker):
        """Fetch a single stock by ticker."""
        stocks = self.get_all_stocks()
        ticker = ticker.upper().strip()
        for s in stocks:
            if s['ticker'] == ticker:
                return s
        return None

    def get_nse_companies(self):
        """
        Scrapes the list of companies from the main NSE page.
        Returns a list of dictionaries with 'ticker' and 'name'.
        """
        try:
            response = self.session.get(self.BASE_URL)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            companies = []
            # accepted format based on previous observation: links in the main content
            # The page structure was headers and links. 
            # We'll look for links that match the pattern /nse/*.html but exclude index pages.
            
            # Based on the read_url_content output, the list is effectively a list of links.
            # let's try to be specific.
            
            # Debug: Print first 5 links found
            all_links = soup.find_all('a', href=True)
            print(f"Debug: Found {len(all_links)} links. First 5: {[a['href'] for a in all_links[:5]]}")

            for a in all_links:
                href = a['href']
                text = a.text.strip()
                
                # Normalize href to ensure we catch /nse/ticker.html or just ticker.html if we are on that page (though we are requesting /nse/)
                # The page is https://afx.kwayisi.org/nse/
                # Hrefs might be "ticker.html" or "/nse/ticker.html".
                
                if 'nse' in href and href.endswith('.html'):
                     # Likely a valid link.
                     # Extract ticker.
                     parts = href.split('/')
                     filename = parts[-1] 
                     ticker = filename.replace('.html', '').upper()
                     
                     if ticker in ['INDEX', 'MYS', 'SELECT']:
                         continue
                     
                     # Ensure we have a valid ticker (usually 3-4 chars, uppercase)
                     if len(ticker) > 6 or not ticker.isalpha():
                         continue

                     companies.append({'ticker': ticker, 'name': text, 'url': f"https://afx.kwayisi.org/nse/{filename}"})
            
            # Remove duplicates based on ticker
            unique_companies = {c['ticker']: c for c in companies}.values()
            return list(unique_companies)
            
        except Exception as e:
            print(f"Error fetching company list: {e}")
            return []

    def get_stock_history(self, ticker):
        """
        Scrapes the 10-day history for a given ticker.
        Returns a pandas DataFrame with Date, Volume, Price, Change.
        """
        url = f"{self.BASE_URL}{ticker.lower()}.html"
        try:
            response = self.session.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # The history is usually in a table.
            # Based on standard HTML tables
            tables = soup.find_all('table')
            
            # We need to find the table that looks like historical data
            # Usually commands 'Date', 'Volume', 'Price', 'Change' or similar
            target_table = None
            for i, table in enumerate(tables):
                headers = [th.text.strip() for th in table.find_all('th')]
                print(f"Debug: Table {i} headers: {headers}")
                
                # Case insensitive check
                headers_lower = [h.lower() for h in headers]
                
                # Check for Date AND (Price OR Close)
                # Also accept generic "Date" and "Close" presence
                if any('date' in h for h in headers_lower) and any('price' in h for h in headers_lower) or any('close' in h for h in headers_lower):
                    target_table = table
                    break
            
            # Manual parsing
            if target_table:
                # Manual parsing
                rows = []
                # finding headers
                # We know table 4 headers seem to be columns?
                
                # finding rows
                tbody = target_table.find('tbody')
                tr_list = tbody.find_all('tr') if tbody else target_table.find_all('tr')
                
                print(f"Debug: Found {len(tr_list)} rows in selected table.")
                
                for i, tr in enumerate(tr_list):
                    tds = tr.find_all('td')
                    if not tds:
                        continue
                    
                    # Due to nested structure, we extract only the first text node or use recursive=False
                    # We iterate over the first 5 tds which correspond to our columns
                    current_row = []
                    for td in tds[:5]:
                        # Get direct text
                        text = td.find(text=True, recursive=False)
                        if text:
                            current_row.append(text.strip())
                        else:
                            strings = list(td.stripped_strings)
                            if strings:
                                current_row.append(strings[0])
                            else:
                                current_row.append("")
                    
                    row_data = current_row

                    # We expect Date, Volume, Close, Change, Change%
                    if len(row_data) >= 5:
                        rows.append(row_data)

                if rows:
                    # Assume columns based on observation
                    # Date, Volume, Close, Change, Change%
                    # We can try to map them dynamically but let's stick to standard if consistent
                    # If we have headers, we can try to use them, but they looked messy.
                    
                    df = pd.DataFrame(rows)
                    
                    # Determine columns. 
                    # If 5 cols: Date, Volume, Close, Change, Change%
                    if len(df.columns) == 5:
                        df.columns = ['Date', 'Volume', 'Close', 'Change', 'Change%']
                    elif len(df.columns) == 4:
                        df.columns = ['Date', 'Volume', 'Close', 'Change']
                    else:
                        # Fallback
                        df.columns = [f"Col{j}" for j in range(len(df.columns))]
                        if 'Date' not in df.columns:
                            # Try 1st col as Date
                            df.rename(columns={'Col0': 'Date'}, inplace=True)
                        if 'Col2' in df.columns and 'Close' not in df.columns:
                            # Try 3rd col as Close (index 2)
                            df.rename(columns={'Col2': 'Close'}, inplace=True)
                    
                    if 'Date' in df.columns:
                        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
                    
                    # Clean numeric columns
                    for col in ['Price', 'Close', 'Volume', 'Low', 'High', 'Open', 'Change']:
                        if col in df.columns:
                            # Remove commas and non-numeric chars except dot and minus
                            # Also handle the triangle symbol which might be in the Change column
                            df[col] = df[col].astype(str).str.replace(r'[^\d.-]', '', regex=True)
                            df[col] = pd.to_numeric(df[col], errors='coerce')

                    return df
                
                return df
                
            print(f"No historical data table found for {ticker}")
            return pd.DataFrame()

        except Exception as e:
            # Safely print error
            try:
                print(f"Error fetching history for {ticker}: {str(e).encode('utf-8')}")
                traceback.print_exc()
            except:
                print(f"Error fetching history for {ticker}")
            return pd.DataFrame()

    def get_stock_fundamentals(self, ticker: str) -> dict:
        """
        Scrapes fundamental data from the stock page.
        Returns dict with: eps, pe_ratio, dps, dividend_yield, shares_outstanding, market_cap.
        """
        url = f"{self.BASE_URL}{ticker.lower()}.html"
        result = {
            'ticker': ticker.upper(),
            'eps': None,
            'pe_ratio': None,
            'dps': None,
            'dividend_yield': None,
            'shares_outstanding': None,
            'market_cap': None
        }
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Helper to find value next to label
            def find_value_for_label(soup, labels):
                for label in labels:
                    # Find element containing the label (case insensitive)
                    element = soup.find(string=lambda t: t and label.lower() in t.lower())
                    
                    if element:
                        # The text node was found.
                        # It might be inside a <b>, <span>, or directly in <td>.
                        # We just need the "next" <td> that appears after this element in the HTML source.
                        
                        # Find the next <td> tag occurring after this text node
                        next_td = element.find_next('td')
                        
                        # Verify it's not the PARENT td (if the label is inside a td)
                        if next_td and next_td == element.parent:
                             # If the next td IS the parent, we need the one AFTER that
                             next_td = next_td.find_next('td')
                        
                        if next_td:
                            text = next_td.get_text()
                            val = self._parse_numeric(text)
                            if val is not None:
                                return val
                return None

            result['eps'] = find_value_for_label(soup, ['Earnings Per Share', 'EPS'])
            result['pe_ratio'] = find_value_for_label(soup, ['Price/Earning', 'P/E'])
            result['dps'] = find_value_for_label(soup, ['Dividend Per Share', 'DPS'])
            result['dividend_yield'] = find_value_for_label(soup, ['Dividend Yield'])
            result['shares_outstanding'] = find_value_for_label(soup, ['Shares Outstanding'])
            result['market_cap'] = find_value_for_label(soup, ['Market Capitalization'])

            return result

            return result
            
        except Exception as e:
            print(f"Error fetching fundamentals for {ticker}: {e}")
            return result

    def _parse_numeric(self, value: str) -> float | None:
        """Parse a numeric string, handling M, B, T suffixes and percentages."""
        if not value:
            return None
        
        value = value.strip().replace(',', '').replace('%', '')
        
        multiplier = 1
        if value.endswith('T'):
            multiplier = 1_000_000_000_000
            value = value[:-1]
        elif value.endswith('B'):
            multiplier = 1_000_000_000
            value = value[:-1]
        elif value.endswith('M'):
            multiplier = 1_000_000
            value = value[:-1]
        elif value.endswith('K'):
            multiplier = 1_000
            value = value[:-1]
        
        try:
            return float(value) * multiplier
        except ValueError:
            return None

if __name__ == "__main__":
    fetcher = NSEDataFetcher()
    print("Fetching companies...")
    companies = fetcher.get_nse_companies()
    print(f"Found {len(companies)} companies.")
    if companies:
        print(f"First 5: {[c['ticker'] for c in companies[:5]]}")
        
        test_ticker = "SCOM"
        print(f"\nFetching history for {test_ticker}...")
        df = fetcher.get_stock_history(test_ticker)
        print(df)
