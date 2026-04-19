import pandas as pd
from typing import Optional

# Default inflation rate (Kenya ~6%)
DEFAULT_INFLATION_RATE = 6.0

class MarketAnalyzer:
    def __init__(self, inflation_rate: float = DEFAULT_INFLATION_RATE):
        self.inflation_rate = inflation_rate

    @staticmethod
    def calculate_dividend_yield(dps: float, price: float) -> Optional[float]:
        """Calculate dividend yield: (DPS / Price) * 100"""
        if dps is None or price is None or price <= 0:
            return None
        return (dps / price) * 100

    def is_inflation_beating(self, yield_pct: Optional[float]) -> bool:
        """Returns True if dividend yield beats inflation."""
        if yield_pct is None:
            return False
        return yield_pct > self.inflation_rate

    def analyze_stock(self, ticker: str, df: pd.DataFrame, fundamentals: dict = None):
        """
        Analyzes a single stock's history and fundamentals.
        Returns a dictionary with analysis results.
        """
        if df.empty or len(df) < 3:
            return None

        # Sort by date ascending for calculation
        df = df.sort_values('Date', ascending=True).copy()
        
        latest_price = df.iloc[-1]['Close']
        latest_date = df.iloc[-1]['Date']
        
        # Calculate SMA (Short Simple Moving Average) - 5 day
        df['SMA_5'] = df['Close'].rolling(window=5).mean()
        current_sma = df.iloc[-1]['SMA_5']
        
        # Trend Detection
        is_uptrend = latest_price > current_sma if pd.notnull(current_sma) else False
        
        # Momentum: Latest change is positive
        try:
            momentum_positive = df.iloc[-1]['Change'] > 0
        except (KeyError, ValueError, TypeError, IndexError):
            momentum_positive = False

        # Volatility: Standard deviation of last 5 days
        volatility = df['Close'].tail(5).std()
        
        # Change percentage
        try:
            change_pct_str = str(df.iloc[-1]['Change%']).replace('%', '').replace('+', '')
            change_pct = float(change_pct_str)
        except (ValueError, TypeError):
            change_pct = 0.0
        
        # Dividend analysis
        dps = fundamentals.get('dps') if fundamentals else None
        dividend_yield = fundamentals.get('dividend_yield') if fundamentals else None
        
        # If we have DPS but no yield, calculate it
        if dps and not dividend_yield:
            dividend_yield = self.calculate_dividend_yield(dps, latest_price)
        
        beats_inflation = self.is_inflation_beating(dividend_yield)
        
        # Buy signals
        # 1. Uptrend + Momentum (Technical)
        # 2. Dividend Yield beats inflation (Value)
        buy_signal_technical = is_uptrend and momentum_positive
        buy_signal_value = beats_inflation
        buy_signal = buy_signal_technical or buy_signal_value
        
        # Alert signals
        alert_signal = False
        alert_reason = ""
        
        if abs(change_pct) > 5.0:
            alert_signal = True
            alert_reason = f"Large movement ({change_pct:+.2f}%)"
        elif volatility > (latest_price * 0.05):
            alert_signal = True
            alert_reason = "High Volatility"

        return {
            'ticker': ticker,
            'date': latest_date,
            'price': latest_price,
            'change_pct': change_pct,
            'is_uptrend': is_uptrend,
            'dps': dps,
            'dividend_yield': dividend_yield,
            'beats_inflation': beats_inflation,
            'buy_signal': buy_signal,
            'buy_signal_technical': buy_signal_technical,
            'buy_signal_value': buy_signal_value,
            'alert_signal': alert_signal,
            'alert_reason': alert_reason,
            'market_cap': fundamentals.get('market_cap') if fundamentals else None
        }

    def analyze_market(self, stock_data_dict: dict, fundamentals_dict: dict = None):
        """
        Analyzes a dictionary of {ticker: df} with optional fundamentals.
        Returns summary lists.
        """
        opportunities = []
        value_stocks = []
        alerts = []
        gainers = []
        losers = []
        
        fundamentals_dict = fundamentals_dict or {}
        
        for ticker, df in stock_data_dict.items():
            fundamentals = fundamentals_dict.get(ticker)
            result = self.analyze_stock(ticker, df, fundamentals)
            
            if result:
                # Categorize
                if result['buy_signal_technical']:
                    opportunities.append(result)
                if result['buy_signal_value']:
                    value_stocks.append(result)
                if result['alert_signal']:
                    alerts.append(result)
                
                # Gainers/Losers
                if result['change_pct'] > 0:
                    gainers.append(result)
                elif result['change_pct'] < 0:
                    losers.append(result)
        
        # Sort
        opportunities.sort(key=lambda x: x['change_pct'], reverse=True)
        value_stocks.sort(key=lambda x: (x['dividend_yield'] or 0), reverse=True)
        gainers.sort(key=lambda x: x['change_pct'], reverse=True)
        losers.sort(key=lambda x: x['change_pct'])
        
        return {
            'opportunities': opportunities,
            'value_stocks': value_stocks,
            'alerts': alerts,
            'gainers': gainers[:10],
            'losers': losers[:10]
        }

    def suggest_portfolio(self, budget: float, opportunities: list, max_stocks: int = 5) -> list:
        """
        Suggest how to allocate budget across top opportunities.
        Returns list of allocations with expected dividends.
        """
        if not opportunities or budget <= 0:
            return []
        
        # Take top N stocks
        top_stocks = opportunities[:max_stocks]
        
        # Equal weight allocation
        allocation_per_stock = budget / len(top_stocks)
        
        allocations = []
        for stock in top_stocks:
            price = stock['price']
            if price and price > 0:
                shares = int(allocation_per_stock // price)
                cost = shares * price
                
                # Expected annual dividend (if DPS available)
                dps = stock.get('dps') or 0
                expected_dividend = shares * dps
                
                # Expected yield on investment
                expected_yield = (expected_dividend / cost * 100) if cost > 0 else 0
                
                allocations.append({
                    'ticker': stock['ticker'],
                    'shares': shares,
                    'price': price,
                    'cost': cost,
                    'dps': dps,
                    'expected_dividend': expected_dividend,
                    'expected_yield': expected_yield
                })
        
        return allocations

if __name__ == "__main__":
    # Test with dummy data
    data = {
        'Date': pd.to_datetime(['2026-02-01', '2026-02-02', '2026-02-03', '2026-02-04', '2026-02-05']),
        'Close': [100, 102, 101, 105, 107],
        'Change': [0, 2, -1, 4, 2],
        'Change%': ['0%', '+2%', '-1%', '+4%', '+2%']
    }
    df = pd.DataFrame(data)
    fundamentals = {'dps': 7.0, 'dividend_yield': 6.5}  # 7% yield beats 6% inflation
    
    analyzer = MarketAnalyzer()
    res = analyzer.analyze_stock("TEST", df, fundamentals)
    print(res)
    
    # Test portfolio allocation
    opportunities = [res]
    portfolio = analyzer.suggest_portfolio(100000, opportunities)
    print(f"\nPortfolio allocation for KES 100,000:")
    for alloc in portfolio:
        print(f"  {alloc['ticker']}: {alloc['shares']} shares @ {alloc['price']:.2f} = KES {alloc['cost']:.2f}")
