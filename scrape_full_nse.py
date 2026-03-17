import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
from datetime import datetime

def scrape_full_nse():
    url = "https://afx.kwayisi.org/nse/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        all_data = []
        trs = soup.find_all('tr')
        
        raw_sequence = []
        for tr in trs:
            s_list = [s.strip() for s in tr.stripped_strings]
            # Data rows usually contain specific patterns like prices (digits.digits)
            if len(s_list) > 20: 
                raw_sequence.extend(s_list)
        
        if not raw_sequence:
            return None

        i = 0
        while i < len(raw_sequence):
            item = raw_sequence[i]
            
            # Ticker check: Uppercase, 2-7 chars, not completely numeric
            if item.isupper() and 1 <= len(item) <= 7 and not re.match(r'^\d', item):
                ticker = item
                name = raw_sequence[i+1] if i+1 < len(raw_sequence) else ""
                
                # Look ahead for boundary
                j = i + 2
                block = [ticker, name]
                while j < len(raw_sequence):
                    next_item = raw_sequence[j]
                    # Boundary is the next Ticker
                    if next_item.isupper() and 1 <= len(next_item) <= 7 and not re.match(r'^[+-]?\d', next_item):
                        break
                    block.append(next_item)
                    j += 1
                
                # block: [Ticker, Name, Volume?, Price, Change?]
                nums = block[2:]
                
                price = 0.0
                volume = 0
                change = 0.0
                
                def clean_f(val):
                    try: return float(val.replace(',', '').replace('%', ''))
                    except: return 0.0

                if len(nums) == 1:
                    price = clean_f(nums[0])
                elif len(nums) == 2:
                    # Likely Price, Change OR Volume, Price
                    if '+' in nums[1] or '-' in nums[1]:
                        price = clean_f(nums[0])
                        change = clean_f(nums[1])
                    else:
                        volume = int(clean_f(nums[0]))
                        price = clean_f(nums[1])
                elif len(nums) >= 3:
                    # Likely Volume, Price, Change
                    volume = int(clean_f(nums[0]))
                    price = clean_f(nums[1])
                    change = clean_f(nums[2])
                
                all_data.append({
                    'Ticker': ticker,
                    'Name': name,
                    'Volume': volume,
                    'Price': price,
                    'Change': change
                })
                i = j
            else:
                i += 1

        if not all_data:
            return None

        df = pd.DataFrame(all_data)
        
        # Deduplicate
        df = df.drop_duplicates(subset=['Ticker'])
        
        # Calculate % Change
        df['Change%'] = df.apply(lambda r: (r['Change'] / (r['Price'] - r['Change']) * 100) if (r['Price'] - r['Change']) != 0 else 0, axis=1)
        
        # Sort by Change% DESC
        df = df.sort_values(by='Change%', ascending=False)
        
        return df

    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    df = scrape_full_nse()
    if df is not None:
        print(f"\nNSE Market Analysis - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("=" * 90)
        print(f"{'Ticker':<8} {'Price':>10} {'Change':>10} {'Change%':>10} {'Volume':>12}  {'Name'}")
        print("-" * 90)
        # Top 15 Gainers
        for _, r in df.head(15).iterrows():
             print(f"{r['Ticker']:<8} {r['Price']:>10.2f} {r['Change']:>+10.2f} {r['Change%']:>9.2f}% {r['Volume']:>12,.0f}  {r['Name']}")
        
        print("-" * 90)
        # Specific search for FTGH
        ftgh = df[df['Ticker'] == 'FTGH']
        if not ftgh.empty:
            r = ftgh.iloc[0]
            print(f"FTGH (Ref) {r['Price']:>10.2f} {r['Change']:>+10.2f} {r['Change%']:>9.2f}% {r['Volume']:>12,.0f}  {r['Name']}")
        
        print("=" * 90)
        print(f"Summary: {len(df)} Unique Stocks Analyze")
