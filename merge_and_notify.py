"""
Merge duplicate user records in portfolio.db and send Telegram notification.
User '1' and '5649100063' are the same person.
"""
import sqlite3
import os
import sys
import requests
from dotenv import load_dotenv
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

CANONICAL_USER_ID = os.getenv('TELEGRAM_CHAT_ID', '5649100063')
OLD_USER_ID = '1'
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def merge_users():
    """Merge user '1' holdings into user '5649100063' using weighted avg cost."""
    conn = sqlite3.connect('portfolio.db')
    cur = conn.cursor()
    
    # Get all rows
    cur.execute('SELECT * FROM portfolio')
    rows = cur.fetchall()
    print("=== BEFORE MERGE ===")
    for r in rows:
        print(f"  id={r[0]} user={r[1]} ticker={r[2]} qty={r[3]} avg_cost={r[4]}")
    
    # Build merged holdings
    merged = {}  # ticker -> {qty, total_cost}
    for r in rows:
        ticker = r[2]
        qty = r[3]
        cost = r[4]
        if ticker not in merged:
            merged[ticker] = {'qty': 0, 'total_cost': 0}
        merged[ticker]['qty'] += qty
        merged[ticker]['total_cost'] += qty * cost
    
    # Calculate weighted average costs
    for ticker in merged:
        merged[ticker]['avg_cost'] = merged[ticker]['total_cost'] / merged[ticker]['qty']
    
    print("\n=== MERGED HOLDINGS ===")
    for ticker, data in merged.items():
        print(f"  {ticker}: {data['qty']} shares @ {data['avg_cost']:.2f}")
    
    # Clear the table and re-insert merged data
    cur.execute('DELETE FROM portfolio')
    now = datetime.utcnow().isoformat()
    for ticker, data in merged.items():
        cur.execute(
            'INSERT INTO portfolio (user_id, ticker, quantity, avg_cost, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)',
            (CANONICAL_USER_ID, ticker, data['qty'], data['avg_cost'], now, now)
        )
    
    conn.commit()
    
    # Verify
    cur.execute('SELECT * FROM portfolio')
    rows = cur.fetchall()
    print("\n=== AFTER MERGE ===")
    for r in rows:
        print(f"  id={r[0]} user={r[1]} ticker={r[2]} qty={r[3]} avg_cost={r[4]:.2f}")
    
    conn.close()
    return merged


def fetch_live_prices(tickers):
    """Fetch live prices from RapidAPI."""
    api_key = os.getenv('RAPIDAPI_KEY')
    if not api_key:
        print("No RAPIDAPI_KEY, using avg_cost as fallback.")
        return {}
    
    prices = {}
    headers = {
        "x-rapidapi-host": "nairobi-stock-exchange-nse.p.rapidapi.com",
        "x-rapidapi-key": api_key
    }
    
    try:
        response = requests.get(
            "https://nairobi-stock-exchange-nse.p.rapidapi.com/stocks",
            headers=headers, timeout=30
        )
        data = response.json()
        if data.get('success'):
            for item in data.get('data', []):
                t = item.get('ticker', '').upper()
                if t in tickers:
                    try:
                        prices[t] = float(item.get('price', '0').replace(',', ''))
                    except:
                        pass
    except Exception as e:
        print(f"RapidAPI error: {e}")
    
    return prices


def send_telegram(message):
    """Send message via Telegram."""
    if not BOT_TOKEN or not CHAT_ID:
        print("No Telegram credentials. Skipping.")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        resp = requests.post(url, json={
            "chat_id": CHAT_ID,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }, timeout=30)
        resp.raise_for_status()
        print("Telegram message sent!")
        return True
    except Exception as e:
        print(f"Telegram error: {e}")
        return False


def main():
    # Step 1: Merge
    merged = merge_users()
    
    # Step 2: Fetch live prices
    tickers = list(merged.keys())
    print(f"\nFetching live prices for {tickers}...")
    prices = fetch_live_prices(tickers)
    print(f"Live prices: {prices}")
    
    # Step 3: Build portfolio summary
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    total_value = 0
    total_cost = 0
    lines = [
        "<b>MY PORTFOLIO</b>",
        f"{now}",
        "",
        "<b>HOLDINGS</b>",
    ]
    
    for ticker, data in merged.items():
        live_price = prices.get(ticker, data['avg_cost'])
        value = data['qty'] * live_price
        cost = data['total_cost']
        pnl = value - cost
        pnl_pct = (pnl / cost * 100) if cost > 0 else 0
        
        total_value += value
        total_cost += cost
        
        emoji = "+" if pnl >= 0 else ""
        lines.append(
            f"<b>{ticker}</b>: {data['qty']:.0f} shares @ {data['avg_cost']:.2f}"
        )
        lines.append(
            f"  Now: {live_price:.2f} | Value: {value:,.0f} | P/L: {emoji}{pnl:,.0f} ({emoji}{pnl_pct:.1f}%)"
        )
        lines.append("")
    
    total_pnl = total_value - total_cost
    total_pnl_pct = (total_pnl / total_cost * 100) if total_cost > 0 else 0
    emoji = "+" if total_pnl >= 0 else ""
    
    lines.append("<b>SUMMARY</b>")
    lines.append(f"Total Cost: KES {total_cost:,.0f}")
    lines.append(f"Total Value: KES {total_value:,.0f}")
    lines.append(f"Total P/L: {emoji}{total_pnl:,.0f} ({emoji}{total_pnl_pct:.1f}%)")
    
    message = "\n".join(lines)
    print(f"\n=== TELEGRAM MESSAGE ===\n{message}")
    
    # Step 4: Send
    send_telegram(message)


if __name__ == "__main__":
    main()
