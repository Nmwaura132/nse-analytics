from mystocks_fetcher import MyStocksFetcher
import os
from bs4 import BeautifulSoup

def check_auth_depth():
    fetcher = MyStocksFetcher()
    if fetcher.login():
        print("Login Successful. Fetching KPLC page...")
        # Reuse the session to get the page
        url = "https://live.mystocks.co.ke/stock=KPLC"
        response = fetcher.session.get(url)
        
        # Save authenticated HTML
        with open("kplc_auth.html", "w", encoding="utf-8") as f:
            f.write(response.text)
        print("Saved kplc_auth.html")
        
        # Search for Order Book
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for the Order Book text
        text = soup.get_text()
        if "Order book" in text:
            print("Found 'Order book' section.")
            # Try to find the specific table
            # Usually it's in a div with specific ID or class
            # Based on raw html, it was near "Real-time market data"
            
            # Print nearby text
            idx = text.find("Order book")
            print(f"Context: {text[idx:idx+200]}")
            
    else:
        print("Login Failed. Cannot check depth.")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    check_auth_depth()
