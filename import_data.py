
import pandas as pd
import os
import argparse
from datetime import datetime

class CSVImporter:
    def __init__(self, data_dir='data/history'):
        self.data_dir = data_dir
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            
    def import_investing_csv(self, file_path: str, ticker: str) -> bool:
        """
        Import CSV from Investing.com format.
        Columns often: "Date", "Price", "Open", "High", "Low", "Vol.", "Change %"
        """
        try:
            print(f"Importing {file_path} for {ticker}...")
            df = pd.read_csv(file_path)
            
            # Rename columns to standard
            # Investing.com uses "Price" for Close
            rename_map = {
                'Price': 'Close',
                'Vol.': 'Volume',
                'Change %': 'ChangePct'
            }
            df.rename(columns=rename_map, inplace=True)
            
            # Parse Date
            # Format varies, usually "02/08/2026" or "Feb 08, 2026"
            try:
                df['Date'] = pd.to_datetime(df['Date'])
            except Exception as e:
                print(f"Date parsing failed, trying mixed format: {e}")
                df['Date'] = pd.to_datetime(df['Date'], format='mixed', dayfirst=True)
                
            # Clean numerical columns (remove ',' and 'K'/'M')
            cols = ['Close', 'Open', 'High', 'Low']
            for col in cols:
                if col in df.columns and df[col].dtype == object:
                    df[col] = df[col].str.replace(',', '').astype(float)
                    
            # Clean Volume (handle K, M, B)
            if 'Volume' in df.columns and df['Volume'].dtype == object:
                def parse_volume(v):
                    if pd.isna(v) or v == '-': return 0
                    v = str(v).upper().replace(',', '')
                    if 'K' in v: return float(v.replace('K', '')) * 1000
                    if 'M' in v: return float(v.replace('M', '')) * 1000000
                    if 'B' in v: return float(v.replace('B', '')) * 1000000000
                    return float(v)
                
                df['Volume'] = df['Volume'].apply(parse_volume)
            
            # Sort by Date
            df.sort_values('Date', inplace=True)
            
            # Save standard format
            out_path = os.path.join(self.data_dir, f"{ticker.upper()}.csv")
            df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']].to_csv(out_path, index=False)
            print(f"Successfully saved to {out_path}")
            return True
            
        except Exception as e:
            print(f"Error importing CSV: {e}")
            return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import Historical Data CSV")
    parser.add_argument("file", help="Path to CSV file")
    parser.add_argument("ticker", help="Stock Ticker (e.g., SCOM)")
    
    args = parser.parse_args()
    
    importer = CSVImporter()
    importer.import_investing_csv(args.file, args.ticker)
