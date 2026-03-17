
from dotenv import load_dotenv
load_dotenv()
from rapidapi_fetcher import RapidAPIFetcher
from advanced_algorithms import enhance_stocks
from dataclasses import dataclass
from typing import Optional

@dataclass
class SimpleStock:
    ticker: str
    name: str = ""
    price: float = 0.0
    change: float = 0.0
    change_pct: Optional[float] = 0.0
    volume: float = 0.0
    # Add dummy attributes expected by EnhancedStock conversion if needed
    momentum_score: float = 0
    volume_score: float = 0
    value_score: float = 0
    composite_score: float = 0
    rank: int = 0
    is_gainer: bool = False
    is_loser: bool = False
    is_active: bool = False
    has_dividend: bool = False
    beats_inflation: bool = False

def rank_candidates():
    print("Fetching live data for candidates...")
    fetcher = RapidAPIFetcher()
    all_stocks_data = fetcher.get_all_stocks()
    
    candidate_tickers = ['SCOM', 'CIC', 'CTUM', 'KPLC', 'KEGN', 'TCL', 'KNRE']
    
    # Convert dicts to SimpleStock objects
    simple_stocks = []
    for s in all_stocks_data:
        if s['ticker'] in candidate_tickers:
            # Handle None change_pct
            cpct = s.get('change_pct')
            if cpct is None: cpct = 0.0
            
            ss = SimpleStock(
                ticker=s['ticker'],
                name=s.get('name', ''),
                price=s.get('price', 0.0),
                change=s.get('change', 0.0),
                change_pct=cpct,
                volume=s.get('volume', 0.0)
            )
            simple_stocks.append(ss)
    
    if not simple_stocks:
        print("No candidates found in API response.")
        return

    # Run AI Analysis
    print("Running AI Scoring Models...")
    enhanced, algo = enhance_stocks(simple_stocks)
    
    # Sort by Sharpe Ratio (Pure efficiency)
    enhanced.sort(key=lambda x: x.sharpe_ratio, reverse=True)
    
    print("\n--- AI CANDIDATE RANKING ---")
    print(f"{'Ticker':<6} {'Price':<8} {'Score':<6} {'Sharpe':<6} {'Signal'}")
    print("-" * 50)
    
    for s in enhanced:
        emoji, signal, conf = algo.get_signal(s)
        print(f"{s.ticker:<6} {s.price:<8.2f} {s.composite_score:<6.0f} {s.sharpe_ratio:<6.2f} {emoji} {signal}")

    winner = enhanced[0]
    print(f"\n🏆 TOP PICK: {winner.ticker}")
    print(f"Why: Highest Sharpe Ratio ({winner.sharpe_ratio:.2f}) - Best Risk-Adjusted Return")

if __name__ == "__main__":
    rank_candidates()
