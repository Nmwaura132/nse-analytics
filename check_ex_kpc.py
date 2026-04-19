
from portfolio_manager import PortfolioManager
import os
from dotenv import load_dotenv
import sys

# Set stdout to utf-8
sys.stdout.reconfigure(encoding='utf-8')

def check_port_ex_kpc():
    load_dotenv()
    user_id = os.getenv('TELEGRAM_CHAT_ID') if os.getenv('TELEGRAM_CHAT_ID') else '5649100063'
    pm = PortfolioManager()
    
    print("--- Active Trading Portfolio (Ex-KPC) ---")
    # Get full portfolio
    port = pm.get_portfolio(user_id)
    
    if port:
        # Filter out KPC
        active_holdings = [h for h in port['holdings'] if h['ticker'] != 'KPC']
        
        if not active_holdings:
            print("No active holdings other than KPC.")
            return

        # Recalculate totals
        total_value = sum(h['value'] for h in active_holdings)
        total_cost = sum(h['cost'] for h in active_holdings)
        total_pnl = total_value - total_cost
        total_pnl_pct = (total_pnl / total_cost * 100) if total_cost > 0 else 0
        
        print(f"Total Value: KES {total_value:,.2f}")
        print(f"Total Cost:  KES {total_cost:,.2f}")
        print(f"PnL:         KES {total_pnl:,.2f} ({total_pnl_pct:.2f}%)")
        print("-" * 30)
        for item in active_holdings:
            print(f"{item['ticker']:<5} {item['qty']:>5,.0f} shares | PnL: {item['pnl_pct']:>6.2f}% | Value: {item['value']:,.0f}")
    else:
        print("Portfolio is empty.")

if __name__ == "__main__":
    check_port_ex_kpc()
