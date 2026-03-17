import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple

class Backtester:
    """
    Simulates trading strategies on historical OHLCV data.
    Provides performance metrics to compare against Buy & Hold.
    """
    def __init__(self, initial_capital: float = 100000.0, commission_pct: float = 0.001):
        self.initial_capital = initial_capital
        # NSE average transaction cost is ~0.1% - 0.2%
        self.commission_pct = commission_pct

    def calculate_signals_macd(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculates MACD Crossover strategy signals.
        1 = Buy, -1 = Sell, 0 = Hold
        """
        df = df.copy()
        
        # Calculate MACD (if not already present)
        if 'MACD' not in df.columns or 'Signal_Line' not in df.columns:
            ema12 = df['Close'].ewm(span=12, adjust=False).mean()
            ema26 = df['Close'].ewm(span=26, adjust=False).mean()
            df['MACD'] = ema12 - ema26
            df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()

        # Signal Generation
        # Buy when MACD crosses above Signal Line. Sell when MACD crosses below.
        df['MACD_Hist'] = df['MACD'] - df['Signal_Line']
        
        # Shift histogram to find crossovers
        df['Hist_Prev'] = df['MACD_Hist'].shift(1)
        
        df['Signal'] = 0
        df.loc[(df['MACD_Hist'] > 0) & (df['Hist_Prev'] <= 0), 'Signal'] = 1  # Buy
        df.loc[(df['MACD_Hist'] < 0) & (df['Hist_Prev'] >= 0), 'Signal'] = -1 # Sell
        
        return df

    def calculate_signals_rsi(self, df: pd.DataFrame, overbought: int = 70, oversold: int = 30) -> pd.DataFrame:
        """
        Calculates Mean Reversion RSI Strategy signals.
        1 = Buy, -1 = Sell, 0 = Hold
        """
        df = df.copy()
        
        if 'RSI' not in df.columns:
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))

        df['Signal'] = 0
        
        # Find crossover points to avoid continuous buying/selling
        df['RSI_Prev'] = df['RSI'].shift(1)
        
        # Buy when crossing up from oversold
        df.loc[(df['RSI'] > oversold) & (df['RSI_Prev'] <= oversold), 'Signal'] = 1
        
        # Sell when crossing down from overbought
        df.loc[(df['RSI'] < overbought) & (df['RSI_Prev'] >= overbought), 'Signal'] = -1
        
        return df

    def run_backtest(self, df: pd.DataFrame, strategy: str = 'MACD') -> Dict[str, Any]:
        """
        Runs the simulation and computes equity curve.
        """
        if df.empty:
            return {'error': 'Dataframe is empty'}
            
        # 1. Generate Signals
        if strategy.upper() == 'MACD':
            df = self.calculate_signals_macd(df)
        elif strategy.upper() == 'RSI':
            df = self.calculate_signals_rsi(df)
        else:
            return {'error': f'Unknown strategy: {strategy}'}
            
        # Drop rows with NaN (indicators calculating)
        df = df.dropna(subset=['Signal', 'Close'])
        
        if df.empty:
             return {'error': 'Not enough data for calculation'}

        cash = self.initial_capital
        holdings = 0.0
        portfolio_value = []
        trades = []
        
        buy_and_hold_shares = self.initial_capital / df.iloc[0]['Close']
        
        for index, row in df.iterrows():
            price = row['Close']
            signal = row['Signal']
            
            # Execute Trades
            if signal == 1 and cash > price: # Buy
                # Go all in
                amount_to_invest = cash
                shares = amount_to_invest / price
                cost = amount_to_invest * self.commission_pct
                
                holdings += shares
                cash -= (amount_to_invest + cost)
                
                trades.append({
                    'date': index,
                    'type': 'BUY',
                    'price': price,
                    'shares': shares
                })
                
            elif signal == -1 and holdings > 0: # Sell
                # Sell all
                value = holdings * price
                cost = value * self.commission_pct
                
                cash += (value - cost)
                
                trades.append({
                    'date': index,
                    'type': 'SELL',
                    'price': price,
                    'shares': holdings
                })
                holdings = 0.0
                
            # Record daily value
            current_value = cash + (holdings * price)
            portfolio_value.append({
                'date': index.strftime('%Y-%m-%d') if hasattr(index, 'strftime') else str(index),
                'strategy_value': current_value,
                'baseline_value': buy_and_hold_shares * price
            })
            
        # End of simulation - sell held positions to calculate final PnL
        final_price = df.iloc[-1]['Close']
        if holdings > 0:
            value = holdings * final_price
            cost = value * self.commission_pct
            cash += (value - cost)
            holdings = 0.0
            
        final_strategy_value = cash
        final_baseline_value = buy_and_hold_shares * final_price
        
        return self._calculate_metrics(df, portfolio_value, trades, final_strategy_value, final_baseline_value)
        

    def _calculate_metrics(self, df: pd.DataFrame, portfolio_value: List[dict], trades: List[dict], 
                           strategy_final: float, baseline_final: float) -> Dict[str, Any]:
        """Calculates performance statistics."""
        
        strategy_return_pct = ((strategy_final - self.initial_capital) / self.initial_capital) * 100
        baseline_return_pct = ((baseline_final - self.initial_capital) / self.initial_capital) * 100
        
        # Calculate Drawdown
        p_df = pd.DataFrame(portfolio_value)
        p_df['Peak'] = p_df['strategy_value'].cummax()
        p_df['Drawdown'] = (p_df['strategy_value'] - p_df['Peak']) / p_df['Peak']
        max_drawdown = p_df['Drawdown'].min() * 100
        
        # Calculate Win Rate
        winning_trades = 0
        total_closed_trades = 0
        
        for i in range(1, len(trades), 2): # Pair Buys with Sells
            if i < len(trades):
                buy_price = trades[i-1]['price']
                sell_price = trades[i]['price']
                if sell_price > buy_price:
                    winning_trades += 1
                total_closed_trades += 1
                
        win_rate = (winning_trades / total_closed_trades * 100) if total_closed_trades > 0 else 0
        
        return {
            'metrics': {
                'initial_capital': self.initial_capital,
                'strategy_final_value': strategy_final,
                'baseline_final_value': baseline_final,
                'strategy_return_pct': strategy_return_pct,
                'baseline_return_pct': baseline_return_pct,
                'alpha': strategy_return_pct - baseline_return_pct,
                'max_drawdown_pct': max_drawdown,
                'total_trades': len(trades),
                'win_rate_pct': win_rate
            },
            'equity_curve': portfolio_value,
            'trades': trades
        }

if __name__ == '__main__':
    # Simple test with simulated data
    from history_generator import generate_stock_history
    print("Testing Backtester...")
    df = generate_stock_history("SCOM", 15.00, 0.02, days=365)
    
    bt = Backtester()
    res = bt.run_backtest(df, strategy='MACD')
    
    print("\nMACD Results:")
    print(f"Strategy Return: {res['metrics']['strategy_return_pct']:.2f}%")
    print(f"Buy/Hold Return: {res['metrics']['baseline_return_pct']:.2f}%")
    print(f"Alpha: {res['metrics']['alpha']:.2f}%")
    print(f"Win Rate: {res['metrics']['win_rate_pct']:.1f}% ({res['metrics']['total_trades']} trades)")
    print(f"Max Drawdown: {res['metrics']['max_drawdown_pct']:.2f}%")
