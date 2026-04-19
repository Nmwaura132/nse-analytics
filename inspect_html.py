import requests
from bs4 import BeautifulSoup

def inspect():
    url = "https://afx.kwayisi.org/nse/scom.html"
    try:
        resp = requests.get(url)
        print(f"Status: {resp.status_code}")
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Print all tables raw text to see structure
        tables = soup.find_all('table')
        if len(tables) > 1:
             print("\n--- Table 1 (Fundamentals?) ---")
             print(tables[1].prettify())
        else:
             print("Less than 2 tables found")
            
    except Exception as e:
        print(e)

if __name__ == "__main__":
    inspect()
