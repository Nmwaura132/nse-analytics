"""
Chart Generator for Telegram Bot
Generates matplotlib charts as PNG bytes for sending via Telegram.
"""
import io
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import FancyBboxPatch
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Premium dark theme
DARK_BG = '#0d1117'
CARD_BG = '#161b22'
GRID_COLOR = '#21262d'
TEXT_COLOR = '#c9d1d9'
GREEN = '#3fb950'
RED = '#f85149'
BLUE = '#58a6ff'
PURPLE = '#bc8cff'
ORANGE = '#d29922'
CYAN = '#39d353'

plt.rcParams.update({
    'figure.facecolor': DARK_BG,
    'axes.facecolor': CARD_BG,
    'axes.edgecolor': GRID_COLOR,
    'axes.labelcolor': TEXT_COLOR,
    'text.color': TEXT_COLOR,
    'xtick.color': TEXT_COLOR,
    'ytick.color': TEXT_COLOR,
    'grid.color': GRID_COLOR,
    'grid.alpha': 0.3,
    'font.family': 'sans-serif',
    'font.size': 10,
})


def _fig_to_bytes(fig) -> bytes:
    """Convert matplotlib figure to PNG bytes."""
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                facecolor=fig.get_facecolor(), edgecolor='none')
    buf.seek(0)
    plt.close(fig)
    return buf


def generate_candlestick_chart(df: pd.DataFrame, ticker: str,
                                trend_data: dict = None,
                                current_price: float = None,
                                avg_cost: float = None) -> bytes:
    """
    Generate a candlestick chart with optional trend line and buy price marker.
    
    Args:
        df: DataFrame with Date, Open, High, Low, Close, Volume columns
        ticker: Stock ticker symbol
        trend_data: Optional dict from MLPredictor.analyze_trend()
        current_price: Current live price
        avg_cost: User's average cost (for buy line)
    
    Returns:
        BytesIO PNG image
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 7),
                                     gridspec_kw={'height_ratios': [3, 1]},
                                     sharex=True)
    fig.subplots_adjust(hspace=0.05)
    
    # Reset index if Date is in index
    plot_df = df.copy()
    if 'Date' not in plot_df.columns:
        plot_df = plot_df.reset_index()
    
    plot_df['Date'] = pd.to_datetime(plot_df['Date'])
    
    # Use last 60 trading days for readability
    plot_df = plot_df.tail(60).reset_index(drop=True)
    
    dates = plot_df['Date']
    opens = plot_df['Open']
    highs = plot_df['High']
    lows = plot_df['Low']
    closes = plot_df['Close']
    volumes = plot_df['Volume']
    
    # --- Candlesticks ---
    width = 0.6
    for i in range(len(plot_df)):
        color = GREEN if closes.iloc[i] >= opens.iloc[i] else RED
        
        # Body
        body_bottom = min(opens.iloc[i], closes.iloc[i])
        body_height = abs(closes.iloc[i] - opens.iloc[i])
        if body_height < 0.01:
            body_height = 0.01
        
        ax1.bar(i, body_height, bottom=body_bottom, width=width,
                color=color, edgecolor=color, linewidth=0.5, alpha=0.9)
        
        # Wicks
        ax1.plot([i, i], [lows.iloc[i], highs.iloc[i]],
                 color=color, linewidth=0.8)
    
    # --- Moving Averages ---
    if len(plot_df) >= 7:
        ma7 = closes.rolling(7).mean()
        ax1.plot(range(len(plot_df)), ma7, color=BLUE, linewidth=1.5,
                 label='MA7', alpha=0.8)
    
    if len(plot_df) >= 20:
        ma20 = closes.rolling(20).mean()
        ax1.plot(range(len(plot_df)), ma20, color=PURPLE, linewidth=1.5,
                 label='MA20', alpha=0.8)
    
    # --- Trend Line (from ML) ---
    if trend_data and 'prediction_line' in trend_data:
        pred_line = trend_data['prediction_line']
        # Slice to match our 60-day window
        pred_line = pred_line[-len(plot_df):]
        ax1.plot(range(len(pred_line)), pred_line, color=ORANGE,
                 linewidth=2, linestyle='--', label=f"Trend ({trend_data['trend']})",
                 alpha=0.7)
    
    # --- Buy Price Line ---
    if avg_cost:
        ax1.axhline(y=avg_cost, color=CYAN, linewidth=1.5, linestyle=':',
                     label=f'My Avg Cost: {avg_cost:.2f}', alpha=0.8)
    
    # --- Current Price Annotation ---
    last_close = closes.iloc[-1]
    ax1.annotate(f'  {last_close:.2f}', xy=(len(plot_df)-1, last_close),
                 fontsize=11, fontweight='bold',
                 color=GREEN if last_close >= (avg_cost or last_close) else RED)
    
    # --- Volume Bars ---
    vol_colors = [GREEN if closes.iloc[i] >= opens.iloc[i] else RED
                  for i in range(len(plot_df))]
    ax2.bar(range(len(plot_df)), volumes, color=vol_colors, alpha=0.6, width=width)
    
    # --- Formatting ---
    ax1.set_title(f'{ticker} — Price Chart', fontsize=14, fontweight='bold',
                  pad=15, color=TEXT_COLOR)
    ax1.legend(loc='upper left', fontsize=8, framealpha=0.3,
               facecolor=CARD_BG, edgecolor=GRID_COLOR)
    ax1.grid(True, alpha=0.2)
    ax1.set_ylabel('Price (KES)', fontsize=10)
    
    ax2.set_ylabel('Volume', fontsize=10)
    ax2.grid(True, alpha=0.2)
    
    # X-axis date labels
    tick_positions = np.linspace(0, len(plot_df)-1, min(8, len(plot_df))).astype(int)
    ax2.set_xticks(tick_positions)
    ax2.set_xticklabels([dates.iloc[i].strftime('%b %d') for i in tick_positions],
                        rotation=45, fontsize=8)
    
    # Watermark
    fig.text(0.99, 0.01, 'OpenClaw NSE Bot', fontsize=7, color=GRID_COLOR,
             ha='right', va='bottom', alpha=0.5)
    
    return _fig_to_bytes(fig)


def generate_forecast_chart(df: pd.DataFrame, ticker: str,
                             forecast: dict, trend: dict,
                             avg_cost: float = None) -> bytes:
    """
    Generate a forecast chart showing historical prices + ML prediction.
    
    Args:
        df: Historical DataFrame
        ticker: Stock ticker
        forecast: dict from MLPredictor.predict_next_price()
        trend: dict from MLPredictor.analyze_trend()
        avg_cost: User's avg cost
    
    Returns:
        BytesIO PNG image
    """
    fig, ax = plt.subplots(1, 1, figsize=(12, 6))
    
    plot_df = df.copy()
    if 'Date' not in plot_df.columns:
        plot_df = plot_df.reset_index()
    
    plot_df['Date'] = pd.to_datetime(plot_df['Date'])
    plot_df = plot_df.tail(90).reset_index(drop=True)
    
    dates = plot_df['Date']
    closes = plot_df['Close']
    
    # --- Historical Price Line ---
    ax.plot(range(len(closes)), closes, color=BLUE, linewidth=2,
            label='Historical', alpha=0.9)
    
    # --- Fill area under curve ---
    ax.fill_between(range(len(closes)), closes.min() * 0.98, closes,
                    color=BLUE, alpha=0.05)
    
    # --- Trend Line ---
    if trend and 'prediction_line' in trend:
        pred_line = trend['prediction_line'][-len(closes):]
        ax.plot(range(len(pred_line)), pred_line, color=ORANGE,
                linewidth=2, linestyle='--',
                label=f"Linear Trend ({trend['trend']}, R²={trend['r2']:.2f})")
    
    # --- ML Prediction Point ---
    if forecast and 'predicted_price' in forecast:
        predicted = forecast['predicted_price']
        last_close = forecast['last_close']
        change_pct = forecast['change_forecast'] * 100
        
        # Add prediction point
        pred_x = len(closes)
        pred_color = GREEN if predicted >= last_close else RED
        
        ax.scatter([pred_x], [predicted], color=pred_color, s=150,
                   zorder=5, edgecolors='white', linewidth=2)
        
        # Dashed line from last to prediction
        ax.plot([len(closes)-1, pred_x], [last_close, predicted],
                color=pred_color, linewidth=2, linestyle=':', alpha=0.8)
        
        # Confidence band (simple ± MSE)
        if 'mse' in forecast:
            mse_band = np.sqrt(forecast['mse'])
            ax.fill_between([pred_x - 0.5, pred_x + 0.5],
                           [predicted - mse_band] * 2,
                           [predicted + mse_band] * 2,
                           color=pred_color, alpha=0.15)
        
        # Annotation
        arrow = '↑' if change_pct > 0 else '↓'
        ax.annotate(f'  ML Predicted: {predicted:.2f}\n  ({arrow} {change_pct:+.1f}%)',
                    xy=(pred_x, predicted), fontsize=11, fontweight='bold',
                    color=pred_color,
                    bbox=dict(boxstyle='round,pad=0.3', facecolor=DARK_BG,
                              edgecolor=pred_color, alpha=0.8))
    
    # --- Buy Price Line ---
    if avg_cost:
        ax.axhline(y=avg_cost, color=CYAN, linewidth=1.5, linestyle=':',
                   label=f'My Avg Cost: {avg_cost:.2f}', alpha=0.8)
    
    # --- Formatting ---
    signal = "HOLD"
    if forecast and 'change_forecast' in forecast:
        cf = forecast['change_forecast'] * 100
        if cf > 1: signal = "BUY / HOLD"
        elif cf < -1: signal = "CAUTION"
    
    ax.set_title(f'{ticker} — ML Forecast (Random Forest) | Signal: {signal}',
                 fontsize=14, fontweight='bold', pad=15, color=TEXT_COLOR)
    ax.legend(loc='upper left', fontsize=9, framealpha=0.3,
              facecolor=CARD_BG, edgecolor=GRID_COLOR)
    ax.grid(True, alpha=0.2)
    ax.set_ylabel('Price (KES)', fontsize=10)
    ax.set_xlabel('Trading Days', fontsize=10)
    
    # X-axis labels
    tick_positions = np.linspace(0, len(closes)-1, min(8, len(closes))).astype(int)
    ax.set_xticks(tick_positions)
    ax.set_xticklabels([dates.iloc[i].strftime('%b %d') for i in tick_positions],
                       rotation=45, fontsize=8)
    
    fig.text(0.99, 0.01, 'OpenClaw NSE Bot', fontsize=7, color=GRID_COLOR,
             ha='right', va='bottom', alpha=0.5)
    
    return _fig_to_bytes(fig)


def generate_analysis_chart(df: pd.DataFrame, ticker: str) -> bytes:
    """
    Generate an advanced analysis chart with:
    1. Top: Price + Bollinger Bands + MA20
    2. Bottom: RSI (14) with status zones
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8),
                                     gridspec_kw={'height_ratios': [3, 1]},
                                     sharex=True)
    fig.subplots_adjust(hspace=0.05)
    
    # Data prep
    plot_df = df.copy()
    if 'Date' not in plot_df.columns:
        plot_df = plot_df.reset_index()
    plot_df['Date'] = pd.to_datetime(plot_df['Date'])
    plot_df = plot_df.tail(90).reset_index(drop=True)
    
    dates = plot_df['Date']
    closes = plot_df['Close']
    
    # --- TOP CHART: Price + BB ---
    # Price
    ax1.plot(range(len(plot_df)), closes, color=TEXT_COLOR, linewidth=2, label='Price')
    
    # Bollinger Bands
    if 'BB_Upper' in plot_df.columns:
        upper = plot_df['BB_Upper']
        lower = plot_df['BB_Lower']
        middle = plot_df['BB_Middle']
        
        ax1.plot(range(len(plot_df)), upper, color=GRID_COLOR, linewidth=1, alpha=0.5)
        ax1.plot(range(len(plot_df)), lower, color=GRID_COLOR, linewidth=1, alpha=0.5)
        ax1.plot(range(len(plot_df)), middle, color=PURPLE, linewidth=1.5,
                 label='MA20 (Trend)', linestyle='--', alpha=0.7)
        
        ax1.fill_between(range(len(plot_df)), upper, lower, color=GRID_COLOR, alpha=0.1)
    
    # Current Price Label
    last_close = closes.iloc[-1]
    ax1.annotate(f'{last_close:.2f}', xy=(len(plot_df)-1, last_close),
                 xytext=(5, 0), textcoords='offset points',
                 fontsize=10, fontweight='bold', color=TEXT_COLOR,
                 bbox=dict(boxstyle='round,pad=0.2', facecolor=CARD_BG, alpha=0.8))

    ax1.set_title(f'{ticker} — Technical Analysis (Bollinger Bands + RSI)',
                  fontsize=14, fontweight='bold', pad=15, color=TEXT_COLOR)
    ax1.legend(loc='upper left', fontsize=9, framealpha=0.3,
               facecolor=CARD_BG, edgecolor=GRID_COLOR)
    ax1.grid(True, alpha=0.2)
    ax1.set_ylabel('Price (KES)', fontsize=10)
    
    # --- BOTTOM CHART: RSI ---
    if 'RSI' in plot_df.columns:
        rsi = plot_df['RSI']
        ax2.plot(range(len(plot_df)), rsi, color=BLUE, linewidth=1.5, label='RSI (14)')
        
        # Zones
        ax2.axhline(70, color=RED, linestyle=':', linewidth=1, alpha=0.5)
        ax2.axhline(30, color=GREEN, linestyle=':', linewidth=1, alpha=0.5)
        ax2.fill_between(range(len(plot_df)), 70, 100, color=RED, alpha=0.1)
        ax2.fill_between(range(len(plot_df)), 0, 30, color=GREEN, alpha=0.1)
        
        # Current RSI Label
        last_rsi = rsi.iloc[-1]
        rsi_color = GREEN if last_rsi < 30 else RED if last_rsi > 70 else TEXT_COLOR
        state = "OVERSOLD" if last_rsi < 30 else "OVERBOUGHT" if last_rsi > 70 else "NEUTRAL"
        
        ax2.text(len(plot_df)+1, last_rsi, f'{last_rsi:.1f}\n{state}',
                 va='center', fontsize=9, fontweight='bold', color=rsi_color)
    else:
        ax2.text(0.5, 0.5, 'RSI Data Missing', ha='center', va='center', color=RED)

    ax2.set_ylim(0, 100)
    ax2.set_ylabel('RSI', fontsize=10)
    ax2.grid(True, alpha=0.2)
    ax2.legend(loc='upper left', fontsize=8)
    
    # X-axis
    tick_positions = np.linspace(0, len(plot_df)-1, min(8, len(plot_df))).astype(int)
    ax2.set_xticks(tick_positions)
    ax2.set_xticklabels([dates.iloc[i].strftime('%b %d') for i in tick_positions],
                        rotation=45, fontsize=8)
    
    return _fig_to_bytes(fig)


def generate_portfolio_chart(holdings: list, total_value: float,
                              total_cost: float) -> bytes:
    """
    Generate a dual chart: Pie (allocation) + Bar (P/L per stock).
    
    Args:
        holdings: list of dicts with ticker, qty, avg_cost, current_price, value, pnl, pnl_pct
        total_value: Total portfolio value
        total_cost: Total cost basis
    
    Returns:
        BytesIO PNG image
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    tickers = [h['ticker'] for h in holdings]
    values = [h['value'] for h in holdings]
    pnls = [h['pnl'] for h in holdings]
    pnl_pcts = [h['pnl_pct'] for h in holdings]
    
    # Color palette
    colors = ['#58a6ff', '#3fb950', '#bc8cff', '#d29922', '#f85149',
              '#39d353', '#db6d28', '#8b949e']
    pie_colors = colors[:len(tickers)]
    
    # --- 1. Allocation Pie ---
    wedges, texts, autotexts = ax1.pie(
        values, labels=tickers, autopct='%1.1f%%',
        colors=pie_colors, startangle=90,
        textprops={'color': TEXT_COLOR, 'fontsize': 11, 'fontweight': 'bold'},
        pctdistance=0.75,
        wedgeprops={'edgecolor': DARK_BG, 'linewidth': 2}
    )
    
    for autotext in autotexts:
        autotext.set_fontsize(9)
        autotext.set_color(DARK_BG)
        autotext.set_fontweight('bold')
    
    # Inner circle for donut effect
    centre_circle = plt.Circle((0, 0), 0.55, fc=CARD_BG)
    ax1.add_artist(centre_circle)
    
    # Center text
    total_pnl = total_value - total_cost
    total_pnl_pct = (total_pnl / total_cost * 100) if total_cost > 0 else 0
    pnl_color = GREEN if total_pnl >= 0 else RED
    
    ax1.text(0, 0.08, f'KES {total_value:,.0f}', ha='center', va='center',
             fontsize=14, fontweight='bold', color=TEXT_COLOR)
    ax1.text(0, -0.12, f'{total_pnl:+,.0f} ({total_pnl_pct:+.1f}%)',
             ha='center', va='center', fontsize=11, color=pnl_color)
    
    ax1.set_title('Portfolio Allocation', fontsize=13, fontweight='bold',
                  pad=15, color=TEXT_COLOR)
    
    # --- 2. P/L Bar Chart ---
    bar_colors = [GREEN if p >= 0 else RED for p in pnls]
    bars = ax2.barh(tickers, pnls, color=bar_colors, height=0.5,
                     edgecolor=[c for c in bar_colors], linewidth=0.5, alpha=0.85)
    
    # Add value labels
    for i, (bar, pnl, pct) in enumerate(zip(bars, pnls, pnl_pcts)):
        label_color = GREEN if pnl >= 0 else RED
        sign = '+' if pnl >= 0 else ''
        x_pos = pnl + (max(abs(p) for p in pnls) * 0.05 * (1 if pnl >= 0 else -1))
        ax2.text(x_pos, i, f'{sign}{pnl:.0f} ({sign}{pct:.1f}%)',
                 va='center', fontsize=10, fontweight='bold', color=label_color)
    
    ax2.axvline(x=0, color=GRID_COLOR, linewidth=1)
    ax2.set_title('Profit / Loss (KES)', fontsize=13, fontweight='bold',
                  pad=15, color=TEXT_COLOR)
    ax2.grid(True, axis='x', alpha=0.2)
    ax2.invert_yaxis()
    ax2.set_xlabel('P/L (KES)', fontsize=10)
    
    # Make ticker labels bold
    ax2.tick_params(axis='y', labelsize=12)
    for label in ax2.get_yticklabels():
        label.set_fontweight('bold')
    
    fig.suptitle('MY PORTFOLIO', fontsize=16, fontweight='bold',
                 color=TEXT_COLOR, y=1.02)
    
    fig.text(0.99, 0.01, 'OpenClaw NSE Bot', fontsize=7, color=GRID_COLOR,
             ha='right', va='bottom', alpha=0.5)
    
    fig.tight_layout()
    return _fig_to_bytes(fig)


if __name__ == "__main__":
    # Quick test
    from ml_predictor import MLPredictor
    
    predictor = MLPredictor()
    df = predictor.get_data("SCOM", 33.85, 0.015)
    trend = predictor.analyze_trend(df)
    forecast = predictor.predict_next_price(df)
    
    # Test candlestick
    img = generate_candlestick_chart(df, "SCOM", trend, 33.85, 32.63)
    with open("test_chart.png", "wb") as f:
        f.write(img.read())
    print("Chart saved to test_chart.png")
