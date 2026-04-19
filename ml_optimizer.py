"""
ML Portfolio Optimizer
Uses Modern Portfolio Theory (Markowitz Efficient Frontier) to find the optimal asset allocation.
Objective: Maximize Sharpe Ratio (Return / Risk).
Technical Limit: Short periods (30-90 days) due to data availability.
"""

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from ml_predictor import MLPredictor
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MLOptimizer:
    def __init__(self):
        self.predictor = MLPredictor()

    def get_optimal_allocation(self, tickers: list, budget: float, risk_free_rate: float = 0.10) -> dict:
        """
        Calculate optimal portfolio allocation to maximize Sharpe Ratio.
        
        Args:
            tickers: List of stock symbols (e.g. ['SCOM', 'EQTY', 'KCB'])
            budget: Total investment amount (e.g. 100000)
            risk_free_rate: Annual risk-free rate (e.g. 10% for T-Bills)
            
        Returns:
            dict containing:
                - allocations: List of {ticker, weight, amount, shares}
                - metrics: {expected_return, volatility, sharpe_ratio}
        """
        if not tickers or len(tickers) < 2:
            return {'error': 'Need at least 2 stocks to optimize.'}

        # 1. Fetch Data
        data = {}
        for ticker in tickers:
            df = self.predictor.get_data(ticker)
            if df is not None and not df.empty:
                data[ticker] = df['Close']
                logger.info(f"Fetched {len(df)} rows for {ticker}")
            else:
                logger.warning(f"No data found for {ticker}")
        
        if len(data) < 2:
            return {'error': f'Need at least 2 stocks with data. Found: {list(data.keys())}'}

        # Create DataFrame of Closing Prices
        prices_df = pd.DataFrame(data)
        
        # 2. Calculate Returns (Daily)
        returns = prices_df.pct_change().dropna()
        
        if returns.empty:
            return {'error': 'Not enough historical data to calculate returns.'}

        # Annualized Mean Returns and Covariance Matrix
        # Assuming 252 trading days
        mean_returns = returns.mean() * 252
        cov_matrix = returns.cov() * 252
        
        num_assets = len(tickers)
        
        # 3. Optimization Function (Minimize Negative Sharpe)
        def negative_sharpe(weights):
            p_return = np.sum(mean_returns * weights)
            p_volatility = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
            sharpe = (p_return - risk_free_rate) / p_volatility
            return -sharpe # Minimize negative Sharpe

        # Constraints: Sum of weights = 1
        constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
        
        # Bounds: 0 <= weight <= 1 (No short selling)
        bounds = tuple((0.0, 1.0) for _ in range(num_assets))
        
        # Initial Guess: Equal distribution
        init_guess = num_assets * [1. / num_assets,]
        
        # Run Optimization
        result = minimize(negative_sharpe, init_guess, method='SLSQP', bounds=bounds, constraints=constraints)
        
        if not result.success:
            return {'error': 'Optimization failed to converge.'}
            
        optimal_weights = result.x
        
        # 4. Compile Results
        p_return = np.sum(mean_returns * optimal_weights)
        p_volatility = np.sqrt(np.dot(optimal_weights.T, np.dot(cov_matrix, optimal_weights)))
        p_sharpe = (p_return - risk_free_rate) / p_volatility
        
        allocations = []
        last_prices = prices_df.iloc[-1]
        
        for i, ticker in enumerate(tickers):
            weight = optimal_weights[i]
            amount = budget * weight
            price = last_prices[ticker]
            shares = int(amount / price) if price > 0 else 0
            
            if weight > 0.01: # Filter out negligible weights
                allocations.append({
                    'ticker': ticker,
                    'weight': round(weight, 4),
                    'percentage': round(weight * 100, 1),
                    'amount': round(amount, 2),
                    'shares': shares,
                    'price': price
                })
        
        # Sort by weight descending
        allocations.sort(key=lambda x: x['weight'], reverse=True)
        
        return {
            'allocations': allocations,
            'metrics': {
                'expected_annual_return': round(p_return * 100, 2),
                'annual_volatility': round(p_volatility * 100, 2),
                'sharpe_ratio': round(p_sharpe, 2),
                'risk_free_rate': round(risk_free_rate * 100, 1)
            },
            'optimized_budget': budget
        }

if __name__ == "__main__":
    # Test
    opt = MLOptimizer()
    res = opt.get_optimal_allocation(['SCOM', 'EQTY', 'KCB', 'EABL'], 100000)
    import json
    print(json.dumps(res, indent=2))
