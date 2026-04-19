from portfolio_manager import PortfolioManager
import os
from dotenv import load_dotenv
import sys

# Set stdout to utf-8
sys.stdout.reconfigure(encoding='utf-8')

def check_port():
    load_dotenv()
    user_id = os.getenv('TELEGRAM_CHAT_ID')
    pm = PortfolioManager()
    
    print("--- Current Portfolio (Safe Print) ---")
    port = pm.get_portfolio(user_id)
    if port:
        print(f"Total Value: KES {port['total_value']:,.2f}")
        print(f"Total Cost:  KES {port['total_cost']:,.2f}")
        print(f"PnL:         KES {port['total_pnl']:,.2f} ({port['total_pnl_pct']:.2f}%)")
        print(f"Risk Score:  {port['risk_score']:.0f}/100")
        print("-" * 30)
        for item in port['holdings']:
            print(f"{item['ticker']:<5} {item['qty']:>5,.0f} shares | PnL: {item['pnl_pct']:>6.2f}% | Value: {item['value']:,.0f}")
    else:
        print("Portfolio is empty.")

if __name__ == "__main__":
    check_port()
