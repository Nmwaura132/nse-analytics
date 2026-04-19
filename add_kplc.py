from portfolio_manager import PortfolioManager
import os
from dotenv import load_dotenv

def add_kplc():
    load_dotenv()
    user_id = os.getenv('TELEGRAM_CHAT_ID')
    pm = PortfolioManager()
    
    print("--- Adding KPLC ---")
    success, msg = pm.add_trade(user_id, "KPLC", 58, 17.55)
    # Safe print
    print(msg.encode('utf-8', 'ignore').decode('utf-8'))
    
    print("\n--- Final Portfolio ---")
    port = pm.get_portfolio(user_id)
    if port:
        for item in port['holdings']:
            print(f"{item['ticker']}: {item['qty']} shares @ {item['avg_cost']:.2f}")

if __name__ == "__main__":
    add_kplc()
