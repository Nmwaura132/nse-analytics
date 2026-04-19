from portfolio_manager import PortfolioManager
import os
from dotenv import load_dotenv

def execute_trades():
    load_dotenv()
    user_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not user_id:
        print("Error: TELEGRAM_CHAT_ID not found in .env")
        return

    pm = PortfolioManager()
    
    # Trade 1: ABSA, 34 shares @ 29.00
    print("--- Executing Trade 1: ABSA ---")
    success, msg = pm.add_trade(user_id, "ABSA", 34, 29.00)
    print(msg)
    
    # Trade 2: KPLC, 58 shares @ 17.55
    print("\n--- Executing Trade 2: KPLC ---")
    success, msg = pm.add_trade(user_id, "KPLC", 58, 17.55)
    print(msg)
    
    # Verify Portfolio
    print("\n--- Current Portfolio ---")
    port = pm.get_portfolio(user_id)
    if port:
        for item in port['holdings']:
            print(f"{item['ticker']}: {item['qty']} shares @ {item['avg_cost']:.2f} (Value: {item['value']:.2f})")
            
        print(f"\nTotal Value: {port['total_value']:.2f}")
        print(f"Total Cost: {port['total_cost']:.2f}")
    else:
        print("Portfolio is empty.")

if __name__ == "__main__":
    execute_trades()
