from portfolio_manager import PortfolioManager
from database import PortfolioItem

def debug_alerts():
    pm = PortfolioManager()
    db = pm.get_db()
    
    # Get users
    user_ids = [u[0] for u in db.query(PortfolioItem.user_id).distinct().all()]
    print(f"Users in DB: {user_ids}")
    
    for user_id in user_ids:
        print(f"\nChecking alerts for User: {user_id}")
        
        # Manually verify portfolio
        port = pm.get_portfolio(user_id)
        if port:
            print(f"Portfolio Items: {len(port['holdings'])}")
            for item in port['holdings']:
                print(f"  {item['ticker']}: P/L {item['pnl_pct']:.2f}%")
        else:
            print("  No portfolio.")
            
        # Check alerts (dry run logic)
        # Note: calling pm.check_alerts might update throttling cache if I'm not careful.
        # But I just want to see logic.
        
        # Re-implement simplified logic to see what SHOULD match
        stocks = pm.analyzer.analyze_all_stocks()
        print(f"Analyzed {len(stocks)} stocks.")
        
        big_movers = [s for s in stocks if s.change_pct and abs(s.change_pct) >= 5.0]
        print(f"Stocks moving > 5%: {[f'{s.ticker} ({s.change_pct}%)' for s in big_movers]}")
        
        # Check if pm.check_alerts returns anything
        # (This uses the real cache, so it might block if already throttled)
        # But wait, separate process has separate memory?
        # Yes! 'python debug_alerts.py' runs in NEW process.
        # It has its own 'self.last_alerts = {}'.
        # So throttling will NOT block (cache empty).
        
        alerts = pm.check_alerts(user_id)
        print(f"Generated Alerts: {alerts}")

if __name__ == "__main__":
    debug_alerts()
