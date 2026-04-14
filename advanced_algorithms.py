"""
Advanced Portfolio Algorithms for NSE Stock Analysis
Implements: Sharpe Ratio, Kelly Criterion, Risk-Adjusted Returns, 
            Modified MPT, Momentum-Volume Correlation
"""
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
import math


@dataclass
class EnhancedStock:
    """Enhanced stock data with advanced metrics."""
    ticker: str
    name: str
    price: float
    change: float
    volume: float
    change_pct: Optional[float] = None
    
    # Computed scores
    momentum_score: float = 0
    volume_score: float = 0
    value_score: float = 0
    composite_score: float = 0
    rank: int = 0
    
    # Advanced metrics
    volatility_estimate: float = 0  # Estimated from price/change ratio
    sharpe_ratio: float = 0         # Risk-adjusted return
    kelly_fraction: float = 0       # Optimal position size
    risk_score: float = 50          # 0-100, higher = riskier
    confidence: float = 50          # Prediction confidence 0-100
    
    # Flags
    is_gainer: bool = False
    is_loser: bool = False
    is_active: bool = False
    has_dividend: bool = False
    beats_inflation: bool = False


class AdvancedPortfolioAlgorithms:
    """
    Advanced algorithms for portfolio allocation and stock analysis.

    Sharpe note:
        We annualise the single-day return with a *persistence factor* that
        conservatively assumes only a fraction of today's move recurs over
        the year.  0.05 (5 %) was too aggressive — it made almost every stock
        Sharpe-negative even on up days.  0.15 (15 %) keeps signals in a
        realistic range while still dampening the raw 252× annualisation.
    Kelly note:
        When a stock is *rising* we use the full absolute change as the
        expected gain; when *falling* we use half the absolute change as the
        "potential bounce" gain and the full change as the expected loss.
        This explicit asymmetry reflects the observed fat-left tail on NSE.
    """

    RISK_FREE_RATE = 0.12          # Kenya 91-day T-Bill rate ~12 %
    INFLATION_RATE = 0.06          # Current inflation ~6 %
    # Conservative daily-return persistence (see class docstring)
    DAILY_PERSISTENCE_FACTOR = 0.15
    
    def __init__(self, stocks: List[EnhancedStock]):
        self.stocks = stocks
        self._compute_market_stats()
    
    def _compute_market_stats(self):
        """Compute market-wide statistics for relative analysis."""
        if not self.stocks:
            return
        
        changes = [s.change for s in self.stocks if s.change is not None]
        volumes = [s.volume for s in self.stocks if s.volume > 0]
        prices = [s.price for s in self.stocks if s.price > 0]
        
        self.avg_change = sum(changes) / len(changes) if changes else 0
        self.avg_volume = sum(volumes) / len(volumes) if volumes else 0
        self.max_volume = max(volumes) if volumes else 1
        self.avg_price = sum(prices) / len(prices) if prices else 0
        
        # Standard deviation of changes (proxy for market volatility)
        if len(changes) > 1:
            variance = sum((c - self.avg_change) ** 2 for c in changes) / len(changes)
            self.market_volatility = math.sqrt(variance)
        else:
            self.market_volatility = 1
    
    def calculate_volatility_estimate(self, stock: EnhancedStock) -> float:
        """
        Estimate volatility from single-day data.
        Uses |change|/price as proxy for daily volatility.
        Annualized = daily * sqrt(252)
        """
        if stock.price <= 0:
            return 0
        
        daily_volatility = abs(stock.change) / stock.price
        # Annualize (252 trading days)
        annualized = daily_volatility * math.sqrt(252)
        return min(annualized, 2.0)  # Cap at 200%
    
    def calculate_sharpe_ratio(self, stock: EnhancedStock) -> float:
        """
        Calculate Sharpe Ratio: (Return - Risk_Free) / Volatility
        
        Higher is better:
        - < 0: Bad
        - 0-1: Acceptable
        - 1-2: Good
        - > 2: Excellent
        """
        if stock.price <= 0:
            return 0
        
        # Annualise daily return with persistence damping (see class docstring)
        daily_return = stock.change / stock.price
        annual_return = daily_return * 252 * self.DAILY_PERSISTENCE_FACTOR

        # Get volatility
        volatility = self.calculate_volatility_estimate(stock)
        if volatility <= 0:
            volatility = 0.01  # Avoid division by zero

        # Sharpe = (Annual Return − Risk-Free Rate) / Volatility
        sharpe = (annual_return - self.RISK_FREE_RATE) / volatility

        # Cap to a reasonable display range
        return max(min(sharpe, 5.0), -5.0)
    
    def calculate_kelly_fraction(self, stock: EnhancedStock) -> float:
        """
        Kelly Criterion for position sizing.
        f* = (bp - q) / b
        
        Where:
        - b = odds (expected return / risk)
        - p = probability of winning
        - q = probability of losing (1-p)
        
        Returns fraction of portfolio (0-1) to allocate.
        """
        if stock.price <= 0:
            return 0
        
        # Estimate win probability from momentum and market context
        if stock.change > 0:
            # Positive momentum → higher win probability (max 75 %)
            p = 0.5 + min(stock.momentum_score / 200, 0.25)
        else:
            # Negative momentum → lower win probability (min 25 %)
            p = 0.5 - min(abs(stock.change) / stock.price * 10, 0.25)

        q = 1 - p

        # Expected gain/loss ratio (odds) — see class docstring for asymmetry rationale
        # Rising stock: full move as potential gain, half move as potential loss.
        # Falling stock: half move as potential bounce gain, full move as expected loss.
        if stock.change > 0:
            expected_gain = abs(stock.change)
            expected_loss = abs(stock.change) * 0.5
        else:
            expected_gain = abs(stock.change) * 0.5
            expected_loss = abs(stock.change)

        if expected_loss <= 0:
            expected_loss = 0.01

        b = expected_gain / expected_loss

        if b <= 0:
            return 0

        # Kelly formula: f* = (bp - q) / b
        f = (b * p - q) / b

        # Quarter-Kelly for safety (reduces position size × 4 to limit ruin risk)
        f = f * 0.25

        # Hard cap: never allocate more than 25 % of portfolio to a single position
        return max(min(f, 0.25), 0)
    
    def calculate_risk_score(self, stock: EnhancedStock) -> float:
        """
        Calculate risk score 0-100 (higher = riskier).
        
        Considers:
        - Volatility (high change = risky)
        - Liquidity (low volume = risky)
        - Price level (penny stocks = risky)
        """
        risk = 50  # Base risk
        
        # Volatility component (0-30 points)
        if stock.price > 0:
            volatility_pct = abs(stock.change) / stock.price * 100
            risk += min(volatility_pct * 3, 30)
        
        # Liquidity component (-20 to +20)
        if self.max_volume > 0:
            liquidity = stock.volume / self.max_volume
            if liquidity < 0.1:
                risk += 20  # Very illiquid
            elif liquidity > 0.5:
                risk -= 20  # Very liquid
        
        # Penny stock component
        if stock.price < 5:
            risk += 15  # Penny stocks are riskier
        elif stock.price > 100:
            risk -= 10  # Blue chips safer
        
        return max(min(risk, 100), 0)
    
    def calculate_confidence(self, stock: EnhancedStock) -> float:
        """
        Calculate prediction confidence 0-100.
        
        Higher confidence when:
        - High trading volume (market agrees)
        - Clear momentum direction
        - Low volatility
        """
        confidence = 50  # Base
        
        # Volume contribution
        if self.max_volume > 0:
            volume_factor = stock.volume / self.max_volume
            confidence += volume_factor * 25  # Max +25
        
        # Clear direction (not flat)
        if stock.price > 0:
            direction_clarity = abs(stock.change) / stock.price * 100
            confidence += min(direction_clarity * 5, 15)  # Max +15
        
        # Momentum alignment
        if (stock.change > 0 and stock.momentum_score > 60) or \
           (stock.change < 0 and stock.momentum_score < 40):
            confidence += 10  # Aligned signal
        
        return max(min(confidence, 95), 10)  # Cap 10-95
    
    def analyze_stock(self, stock: EnhancedStock) -> EnhancedStock:
        """Apply all advanced metrics to a stock."""
        stock.volatility_estimate = self.calculate_volatility_estimate(stock)
        stock.sharpe_ratio = self.calculate_sharpe_ratio(stock)
        stock.kelly_fraction = self.calculate_kelly_fraction(stock)
        stock.risk_score = self.calculate_risk_score(stock)
        stock.confidence = self.calculate_confidence(stock)
        return stock
    
    def get_optimal_allocation(self, budget: float, max_stocks: int = 5) -> dict:
        """
        Calculate optimal portfolio allocation using risk parity.
        
        Strategy:
        1. Filter to best candidates (positive Sharpe, reasonable risk)
        2. Weight by inverse volatility (risk parity concept)
        3. Apply Kelly fraction limits
        4. Return allocation with expected metrics
        """
        # Apply advanced metrics to all stocks
        analyzed = [self.analyze_stock(s) for s in self.stocks]
        
        # Filter candidates: positive expected return, reasonable risk
        candidates = [
            s for s in analyzed 
            if s.sharpe_ratio > 0 
            and s.risk_score < 80 
            and s.price > 0
            and s.kelly_fraction > 0
        ]
        
        if not candidates:
            # Fallback to top by composite score
            candidates = sorted(analyzed, key=lambda x: x.composite_score, reverse=True)[:max_stocks]
        
        # Sort by Sharpe ratio (risk-adjusted return)
        candidates = sorted(candidates, key=lambda x: x.sharpe_ratio, reverse=True)[:max_stocks]
        
        # Risk parity: weight inversely by volatility
        total_inv_vol = sum(1 / max(c.volatility_estimate, 0.01) for c in candidates)
        
        allocations = []
        total_allocated = 0
        
        for stock in candidates:
            # Base weight from risk parity
            inv_vol = 1 / max(stock.volatility_estimate, 0.01)
            weight = inv_vol / total_inv_vol
            
            # Apply Kelly fraction limit
            weight = min(weight, stock.kelly_fraction * 4)  # 4x fractional Kelly
            
            # Calculate shares and cost
            allocated = budget * weight
            shares = int(allocated // stock.price)
            cost = shares * stock.price
            total_allocated += cost
            
            if shares > 0:
                allocations.append({
                    'stock': stock,
                    'shares': shares,
                    'cost': cost,
                    'weight': cost / budget,
                    'expected_return': stock.sharpe_ratio * stock.volatility_estimate,
                    'risk': stock.risk_score
                })
        
        # Calculate portfolio metrics
        if allocations:
            portfolio_return = sum(a['weight'] * a['expected_return'] for a in allocations)
            portfolio_risk = sum(a['weight'] * a['risk'] for a in allocations)
            weighted_sharpe = sum(a['weight'] * a['stock'].sharpe_ratio for a in allocations)
        else:
            portfolio_return = 0
            portfolio_risk = 50
            weighted_sharpe = 0
        
        return {
            'allocations': allocations,
            'total_invested': total_allocated,
            'cash_remaining': budget - total_allocated,
            'portfolio_expected_return': portfolio_return,
            'portfolio_risk_score': portfolio_risk,
            'portfolio_sharpe': weighted_sharpe,
            'holding_period': self._recommend_holding_period(portfolio_risk, weighted_sharpe)
        }
    
    def _recommend_holding_period(self, risk: float, sharpe: float) -> dict:
        """Recommend holding period based on portfolio characteristics."""
        if sharpe > 1.5 and risk < 40:
            return {
                'period': "1-4 weeks",
                'type': "SHORT TERM",
                'emoji': "⚡",
                'reason': "High Sharpe ratio with low risk - capture quick gains"
            }
        elif sharpe > 0.5 and risk < 60:
            return {
                'period': "1-3 months",
                'type': "MEDIUM TERM",
                'emoji': "📅",
                'reason': "Good risk-adjusted returns - allow trends to develop"
            }
        else:
            return {
                'period': "6-12 months",
                'type': "LONG TERM", 
                'emoji': "📆",
                'reason': "Higher risk or lower Sharpe - hold for value appreciation"
            }
    
    def get_signal(self, stock: EnhancedStock) -> Tuple[str, str, int]:
        """
        Generate trading signal with confidence.
        
        Returns: (emoji, signal_text, confidence)
        """
        self.analyze_stock(stock)
        
        sharpe = stock.sharpe_ratio
        risk = stock.risk_score
        confidence = int(stock.confidence)
        
        if sharpe > 1.5 and risk < 40:
            return ("🚀", "STRONG BUY", min(confidence + 15, 95))
        elif sharpe > 0.5 and risk < 60:
            return ("📈", "BUY", confidence)
        elif sharpe > 0 and risk < 70:
            return ("↗️", "HOLD/BUY", max(confidence - 10, 20))
        elif sharpe < -0.5 or risk > 80:
            return ("📉", "SELL", confidence)
        elif sharpe < 0:
            return ("↘️", "HOLD/SELL", max(confidence - 15, 20))
        else:
            return ("➡️", "HOLD", 50)


# Integration helper
def enhance_stocks(stocks: list) -> Tuple[List[EnhancedStock], AdvancedPortfolioAlgorithms]:
    """Convert basic stocks to enhanced stocks and create analyzer."""
    enhanced = []
    for s in stocks:
        es = EnhancedStock(
            ticker=s.ticker,
            name=s.name,
            price=s.price,
            change=s.change,
            change_pct=s.change_pct,
            volume=s.volume,
            momentum_score=s.momentum_score,
            volume_score=s.volume_score,
            value_score=s.value_score,
            composite_score=s.composite_score,
            rank=s.rank,
            is_gainer=s.is_gainer,
            is_loser=s.is_loser,
            is_active=s.is_active,
            has_dividend=s.has_dividend,
            beats_inflation=s.beats_inflation
        )
        enhanced.append(es)
    
    algo = AdvancedPortfolioAlgorithms(enhanced)
    return enhanced, algo
