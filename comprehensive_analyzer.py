"""
Comprehensive NSE Stock Analyzer
Combines RapidAPI real-time data with advanced scoring metrics.
"""
import os
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

from tradingview_fetcher import TradingViewFetcher
from data_fetcher import NSEDataFetcher
from rapidapi_fetcher import RapidAPIFetcher


@dataclass
class StockScore:
    """Composite scoring for a stock."""
    ticker: str
    name: str
    price: float
    volume: float
    change: float
    change_pct: Optional[float]
    
    # Scores (0-100)
    momentum_score: float = 0  # Based on price movement
    volume_score: float = 0    # Based on trading activity
    value_score: float = 0     # Based on DPS/yield
    composite_score: float = 0 # Weighted combination
    
    # Signals
    is_gainer: bool = False
    is_loser: bool = False
    is_active: bool = False
    has_dividend: bool = False
    beats_inflation: bool = False
    
    # Fundamentals (if available)
    dps: Optional[float] = None
    dividend_yield: Optional[float] = None
    pe_ratio: Optional[float] = None
    market_cap: Optional[float] = None
    
    # Rank
    rank: int = 0


class ComprehensiveAnalyzer:
    """
    Analyzes all NSE stocks and produces comprehensive rankings.
    """
    
    # Kenya inflation rate for comparison
    INFLATION_RATE = 6.0
    
    # Scoring weights
    WEIGHT_MOMENTUM = 0.35
    WEIGHT_VOLUME = 0.25
    WEIGHT_VALUE = 0.40
    MIN_PRICE = 2.00  # Exclude stocks below KES 2.0 to avoid junk/pennystocks
    
    def __init__(self):
        self.market_data = RapidAPIFetcher()
        self.afx_fetcher = NSEDataFetcher()
    

    def calculate_momentum_score(
        self,
        change: float,
        min_change: float,
        max_change: float,
    ) -> float:
        """
        Score based on price change relative to market.
        Range: 0-100

        Accepts pre-computed min/max to avoid O(n²) recomputation inside the
        per-stock loop of analyze_all_stocks().
        """
        if change is None:
            return 50  # Neutral

        range_val = max_change - min_change
        if range_val == 0:
            return 50

        score = ((change - min_change) / range_val) * 100
        return max(0, min(100, score))
    
    def calculate_volume_score(self, volume: float, log_max_volume: float) -> float:
        """
        Score based on trading volume relative to market.
        Higher volume = more liquidity = better score.
        Range: 0-100

        Accepts pre-computed log_max_volume to avoid recomputing log(max) for
        every stock in the batch (O(n) instead of O(n²)).
        """
        if volume is None or volume <= 0:
            return 0

        if log_max_volume <= 0:
            return 0

        import math
        log_volume = math.log10(volume + 1)
        score = (log_volume / log_max_volume) * 100
        return max(0, min(100, score))
    
    def calculate_value_score(self, dividend_yield: Optional[float]) -> float:
        """
        Score based on dividend yield.
        Range: 0-100
        """
        if not dividend_yield or dividend_yield <= 0:
            return 0
        
        # Scale: 0% = 0, 6% (inflation) = 50, 12%+ = 100
        if dividend_yield >= 12:
            return 100
        elif dividend_yield >= self.INFLATION_RATE:
            # 6-12% maps to 50-100
            return 50 + ((dividend_yield - self.INFLATION_RATE) / 6) * 50
        else:
            # 0-6% maps to 0-50
            return (dividend_yield / self.INFLATION_RATE) * 50
    
    def fetch_all_data(self) -> List[dict]:
        """Fetch real-time data for all stocks using RapidAPI with fallback."""
        try:
            stocks = self.market_data.get_all_stocks()
            if stocks and len(stocks) > 0:
                return stocks
        except Exception as e:
            print(f"RapidAPI failed: {e}")
        
        print("Falling back to AFX (NSEDataFetcher)...")
        try:
            raw_stocks = self.afx_fetcher.get_nse_companies()
            # Normalize keys to match RapidAPIFetcher format
            normalized = []
            for s in raw_stocks:
                # Exhaustive mapping for AFX/Scraper variations
                price = s.get('price') or s.get('Price') or 0.0
                change = s.get('change') or s.get('Change') or 0.0
                volume = s.get('volume') or s.get('Volume') or 0.0
                
                # Cleanup change_pct
                change_pct = s.get('change_pct') or s.get('Change%') or 0.0
                if isinstance(change_pct, str):
                    try: change_pct = float(change_pct.replace('%', '').replace('+', ''))
                    except: change_pct = 0.0

                normalized.append({
                    'ticker': s.get('ticker') or s.get('Ticker'),
                    'name': s.get('name') or s.get('Name') or "Unknown",
                    'price': float(price),
                    'volume': float(volume),
                    'change': float(change),
                    'change_pct': float(change_pct)
                })
            return normalized
        except Exception as e:
            print(f"Fallback failed: {e}")
            return []

    def analyze_all_stocks(self, include_fundamentals: bool = False) -> List[StockScore]:
        """
        Analyze all stocks and return scored list.
        Pre-computes market-wide statistics once before the per-stock loop
        to avoid O(n²) repeated min/max/log calls.
        """
        print("Fetching real-time market data via RapidAPI...")
        stocks = self.fetch_all_data()

        if not stocks:
            print("No stock data retrieved!")
            return []

        print(f"Retrieved {len(stocks)} stocks. Calculating scores...")

        # --- Pre-compute normalization stats once ---
        import math
        all_changes = [s['change'] for s in stocks]
        all_volumes  = [s['volume'] for s in stocks]

        valid_changes = [c for c in all_changes if c is not None]
        min_change = min(valid_changes) if valid_changes else 0
        max_change = max(valid_changes) if valid_changes else 0

        valid_volumes = [v for v in all_volumes if v and v > 0]
        log_max_volume = math.log10(max(valid_volumes) + 1) if valid_volumes else 1

        results = []

        for stock in stocks:
            ticker = stock['ticker']

            # Use pre-computed stats — O(1) per stock
            momentum = self.calculate_momentum_score(stock['change'], min_change, max_change)
            volume   = self.calculate_volume_score(stock['volume'], log_max_volume)
            
            # Fetch fundamentals if requested (slower)
            dps = None
            dividend_yield = None
            pe_ratio = None
            market_cap = None
            
            if include_fundamentals:
                dividend_yield = stock.get('dividend_yield')
                pe_ratio = stock.get('pe_ratio')
                market_cap = stock.get('market_cap')
                dps = None # We use yield directly
            
            value = self.calculate_value_score(dividend_yield)
            
            # Dynamic Weighting: Redistribute if Value score is 0 due to missing data?
            # If no dividend yield is *present* (None), we shouldn't penalize.
            # But if yield is 0 (known), we should penalize value.
            # Here we only check if value is 0. 
            # Better check: if we failed to fetch fundamentals?
            
            w_mom = self.WEIGHT_MOMENTUM
            w_vol = self.WEIGHT_VOLUME
            w_val = self.WEIGHT_VALUE
            
            # If no fundamental data was fetched (meaning we relied purely on price action)
            # OR if the stock is a growth stock with 0 dividend but high momentum?
            # Let's simplify: If Value score is 0, we lessen its impact if fetches failed.
            if value == 0 and dividend_yield is None:
                # Missing data case -> Redistribute
                total_other = w_mom + w_vol
                if total_other > 0:
                    w_mom += (w_val * (w_mom / total_other))
                    w_vol += (w_val * (w_vol / total_other))
                    w_val = 0
            
            # Composite score
            composite = (
                momentum * w_mom +
                volume * w_vol +
                value * w_val
            )
            
            # Create score object
            p = stock.get('price') or stock.get('Price') or 0.0
            v = stock.get('volume') or stock.get('Volume') or 0.0
            
            # Skip invalid prices or "junk" pennystocks to avoid ZeroDivisionError or high-risk noise
            if p < self.MIN_PRICE:
                continue
                
            score = StockScore(
                ticker=ticker,
                name=stock.get('name') or stock.get('Name') or "Unknown",
                price=float(p),
                volume=float(v),
                change=stock['change'] or 0,
                change_pct=stock.get('change_pct'),
                momentum_score=round(momentum, 1),
                volume_score=round(volume, 1),
                value_score=round(value, 1),
                composite_score=round(composite, 1),
                is_gainer=stock['change'] and stock['change'] > 0,
                is_loser=stock['change'] and stock['change'] < 0,
                is_active=stock['volume'] and stock['volume'] > 100000,
                has_dividend=dividend_yield is not None and dividend_yield > 0,
                beats_inflation=dividend_yield is not None and dividend_yield > self.INFLATION_RATE,
                dps=dps,
                dividend_yield=dividend_yield,
                pe_ratio=pe_ratio,
                market_cap=market_cap
            )
            
            results.append(score)
        
        # Sort by composite score and assign ranks
        results.sort(key=lambda x: x.composite_score, reverse=True)
        for i, score in enumerate(results, 1):
            score.rank = i
        
        return results
    
    def get_top_picks(self, count: int = 10, include_fundamentals: bool = False) -> List[StockScore]:
        """Get top N stocks by composite score."""
        all_scores = self.analyze_all_stocks(include_fundamentals)
        return all_scores[:count]
    
    def get_gainers(self, count: int = 10) -> List[StockScore]:
        """Get top gainers."""
        all_scores = self.analyze_all_stocks()
        gainers = [s for s in all_scores if s.is_gainer]
        gainers.sort(key=lambda x: x.change, reverse=True)
        return gainers[:count]
    
    def get_losers(self, count: int = 10) -> List[StockScore]:
        """Get top losers."""
        all_scores = self.analyze_all_stocks()
        losers = [s for s in all_scores if s.is_loser]
        losers.sort(key=lambda x: x.change)
        return losers[:count]
    
    def get_most_active(self, count: int = 10) -> List[StockScore]:
        """Get most actively traded."""
        all_scores = self.analyze_all_stocks()
        all_scores.sort(key=lambda x: x.volume, reverse=True)
        return all_scores[:count]
    
    def print_report(self, stocks: List[StockScore], title: str = "Stock Analysis"):
        """Print a formatted report."""
        print(f"\n{'='*70}")
        print(f"  {title}")
        print(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"{'='*70}\n")
        
        print(f"{'Rank':<5} {'Ticker':<8} {'Name':<25} {'Price':>10} {'Change':>8} {'Score':>7}")
        print("-" * 70)
        
        for stock in stocks:
            name = stock.name[:24] if len(stock.name) > 24 else stock.name
            change_str = f"{stock.change:+.2f}" if stock.change else "0.00"
            print(f"{stock.rank:<5} {stock.ticker:<8} {name:<25} {stock.price:>10.2f} {change_str:>8} {stock.composite_score:>7.1f}")
        
        print()


def generate_full_analysis():
    """Generate a comprehensive market analysis."""
    analyzer = ComprehensiveAnalyzer()
    
    print("\n" + "="*70)
    print("  NSE COMPREHENSIVE MARKET ANALYSIS")
    print("  " + datetime.now().strftime("%Y-%m-%d %H:%M"))
    print("="*70)
    
    # Fetch and analyze all stocks
    all_stocks = analyzer.analyze_all_stocks()
    
    if not all_stocks:
        print("Failed to retrieve stock data!")
        return None
    
    # Top 10 by composite score
    print("\n[TOP 10] STOCKS (Composite Score)")
    print("-" * 70)
    print(f"{'Rank':<5} {'Ticker':<8} {'Price':>10} {'Chg':>8} {'Mom':>6} {'Vol':>6} {'Val':>6} {'Score':>7}")
    print("-" * 70)
    for s in all_stocks[:10]:
        print(f"{s.rank:<5} {s.ticker:<8} {s.price:>10.2f} {s.change:>+8.2f} {s.momentum_score:>6.0f} {s.volume_score:>6.0f} {s.value_score:>6.0f} {s.composite_score:>7.1f}")
    
    # Top gainers
    gainers = sorted([s for s in all_stocks if s.is_gainer], key=lambda x: x.change, reverse=True)[:5]
    print("\n[GAINERS] TOP 5")
    print("-" * 50)
    for s in gainers:
        print(f"  {s.ticker:8} {s.price:>8.2f}  {s.change:>+6.2f}  {s.name[:30]}")
    
    # Top losers
    losers = sorted([s for s in all_stocks if s.is_loser], key=lambda x: x.change)[:5]
    print("\n[LOSERS] TOP 5")
    print("-" * 50)
    for s in losers:
        print(f"  {s.ticker:8} {s.price:>8.2f}  {s.change:>+6.2f}  {s.name[:30]}")
    
    # Most active
    active = sorted(all_stocks, key=lambda x: x.volume, reverse=True)[:5]
    print("\n[ACTIVE] MOST ACTIVE (by volume)")
    print("-" * 50)
    for s in active:
        vol_str = f"{s.volume:,.0f}" if s.volume else "0"
        print(f"  {s.ticker:8} {s.price:>8.2f}  Vol: {vol_str:>15}")
    
    # Market summary
    total_gainers = len([s for s in all_stocks if s.is_gainer])
    total_losers = len([s for s in all_stocks if s.is_loser])
    unchanged = len(all_stocks) - total_gainers - total_losers
    
    print("\n[SUMMARY] MARKET OVERVIEW")
    print("-" * 50)
    print(f"  Total Stocks: {len(all_stocks)}")
    print(f"  Gainers:      {total_gainers} ({100*total_gainers/len(all_stocks):.1f}%)")
    print(f"  Losers:       {total_losers} ({100*total_losers/len(all_stocks):.1f}%)")
    print(f"  Unchanged:    {unchanged}")
    
    # Best buy candidates (high composite + gaining)
    buy_candidates = [s for s in all_stocks if s.composite_score >= 50 and s.is_gainer]
    buy_candidates.sort(key=lambda x: x.composite_score, reverse=True)
    
    if buy_candidates:
        print("\n[BUY] CANDIDATES (Score >=50, Currently Gaining)")
        print("-" * 50)
        for s in buy_candidates[:5]:
            print(f"  {s.ticker:8} {s.price:>8.2f}  Score: {s.composite_score:.0f}  Change: {s.change:>+.2f}")
    
    print("\n" + "="*70)
    print("  Analysis complete.")
    print("="*70 + "\n")
    
    return all_stocks


if __name__ == "__main__":
    generate_full_analysis()
