import numpy as np
import pandas as pd
from datetime import datetime, timedelta

def generate_stock_history(ticker: str, current_price: float, volatility: float, 
                         days: int = 180, trend: float = 0.0005) -> pd.DataFrame:
    """
    Generate realistic historical OHLCV data using Geometric Brownian Motion.
    
    Args:
        ticker: Stock symbol
        current_price: The latest price to end the simulation at
        volatility: Daily volatility (standard deviation)
        days: Number of historical days to generate
        trend: Daily drift trend (default slightly positive)
        
    Returns:
        DataFrame with Date, Open, High, Low, Close, Volume
    """
    # Create date range (business days)
    end_date = datetime.now()
    dates = pd.date_range(end=end_date, periods=days, freq='B')
    
    # Initialize price array working backwards from current price
    prices = np.zeros(days)
    prices[-1] = current_price
    
    # Generate prices backwards
    # P_t-1 = P_t / exp((mu - 0.5 * sigma^2) + sigma * Z)
    dt = 1
    mu = trend
    sigma = max(volatility, 0.01) # Ensure some volatility
    
    for i in range(days-2, -1, -1):
        shock = np.random.normal(0, 1)
        drift = (mu - 0.5 * sigma**2) * dt
        diffusion = sigma * shock * np.sqrt(dt)
        change = np.exp(drift + diffusion)
        prices[i] = prices[i+1] / change
        
    # Generate OHLC data from daily closing prices
    data = []
    base_volume = 100000 if current_price > 50 else 500000
    
    for i, date in enumerate(dates):
        close_price = prices[i]
        
        # Intra-day volatility for High/Low
        open_price = close_price * (1 + np.random.normal(0, sigma/3))
        
        high_price = max(open_price, close_price) * (1 + abs(np.random.normal(0, sigma/2)))
        low_price = min(open_price, close_price) * (1 - abs(np.random.normal(0, sigma/2)))
        
        # Volume with random spikes
        volume_shock = np.random.lognormal(0, 0.5)
        volume = int(base_volume * volume_shock)
        
        data.append({
            'Date': date,
            'Ticker': ticker,
            'Open': round(open_price, 2),
            'High': round(high_price, 2),
            'Low': round(low_price, 2),
            'Close': round(close_price, 2),
            'Volume': volume
        })
        
    df = pd.DataFrame(data)
    df.set_index('Date', inplace=True)
    return df

if __name__ == "__main__":
    # Test
    df = generate_stock_history("TEST", 100.0, 0.02)
    print(df.head())
    print(df.tail())
