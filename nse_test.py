import yfinance as yf

def test_nse_tickers():
    # Common NSE tickers with potential Yahoo Finance suffixes
    # .NR is often used for Nairobi, sometimes .KZ or others depending on the provider mapping in Yahoo
    tickers_to_test = [
        "SCOM.NR", # Safaricom
        "EQTY.NR", # Equity Group
        "KCB.NR",  # KCB Group
        "EABL.NR", # East African Breweries
        "COOP.NR"  # Co-operative Bank
    ]

    print(f"Testing tickers: {tickers_to_test}")

    for ticker in tickers_to_test:
        try:
            print(f"\nFetching data for {ticker}...")
            stock = yf.Ticker(ticker)
            # Get last 5 days history
            hist = stock.history(period="5d")
            
            if not hist.empty:
                print(f"SUCCESS: Found data for {ticker}")
                print(hist.tail())
            else:
                print(f"FAILED: No data found for {ticker}")
        except Exception as e:
            print(f"ERROR: Failed to fetch {ticker} - {e}")

if __name__ == "__main__":
    test_nse_tickers()
