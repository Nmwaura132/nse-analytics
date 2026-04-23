"""
NSE Dashboard Server
Real-time market dashboard powered by RapidAPI NSE data.
"""
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
import time
from dataclasses import asdict
from datetime import datetime

from comprehensive_analyzer import ComprehensiveAnalyzer, StockScore
from advanced_algorithms import enhance_stocks, AdvancedPortfolioAlgorithms
from data_fetcher import NSEDataFetcher
from tradingview_fetcher import TradingViewFetcher
import financials
from ml_predictor import MLPredictor
from ml_optimizer import MLOptimizer
from portfolio_manager import PortfolioManager
from backtester import Backtester
import pandas as pd
import numpy as np

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)
# predictor = MLPredictor()
# pm = PortfolioManager()
predictor_instance = None
pm_instance = None

def get_predictor():
    global predictor_instance
    if predictor_instance is None:
        from ml_predictor import MLPredictor
        predictor_instance = MLPredictor()
    return predictor_instance

def get_pm():
    global pm_instance
    if pm_instance is None:
        from portfolio_manager import PortfolioManager
        pm_instance = PortfolioManager()
    return pm_instance

# Global cache
market_cache = {
    'last_update': None,
    'stocks': [],
    'enhanced': [],
    'algo': None,
    'summary': {}
}
# Notification queue (in-memory for simplicity)
notifications_queue = []
MAX_NOTIFICATIONS = 50

CACHE_TTL = 120  # 2 minutes (RapidAPI is fast)

# analyzer = ComprehensiveAnalyzer()
# We'll initialize it lazily like we did for the bot
analyzer_instance = None

def get_analyzer():
    global analyzer_instance
    if analyzer_instance is None:
        from comprehensive_analyzer import ComprehensiveAnalyzer
        analyzer_instance = ComprehensiveAnalyzer()
    return analyzer_instance


def stock_to_dict(s: StockScore, enhanced_metrics=None) -> dict:
    """Convert StockScore to serializable dict."""
    data = {
        'ticker': s.ticker,
        'name': s.name,
        'price': s.price,
        'volume': s.volume,
        'change': s.change,
        'change_pct': s.change_pct,
        'momentum_score': s.momentum_score,
        'volume_score': s.volume_score,
        'value_score': s.value_score,
        'composite_score': s.composite_score,
        'is_gainer': s.is_gainer,
        'is_loser': s.is_loser,
        'is_active': s.is_active,
        'has_dividend': s.has_dividend,
        'beats_inflation': s.beats_inflation,
        'dps': s.dps,
        'dividend_yield': s.dividend_yield,
        'pe_ratio': s.pe_ratio,
        'market_cap': s.market_cap,
        'rank': s.rank
    }
    
    if enhanced_metrics:
        data.update(enhanced_metrics)
        
    return data


def sanitize_json(obj):
    """Recursively replace NaN/Infinity with None for valid JSON."""
    if isinstance(obj, float):
        if np.isnan(obj) or np.isinf(obj):
            return None
        return obj
    elif isinstance(obj, dict):
        return {k: sanitize_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_json(v) for v in obj]
    elif isinstance(obj, pd.Series):
        return sanitize_json(obj.to_dict())
    return obj


def refresh_market_data():
    """Fetches and caches market data from TradingView."""
    print("Refreshing market data from TradingView...")
    
    stocks = get_analyzer().analyze_all_stocks()
    
    if not stocks:
        print("Failed to fetch market data!")
        return
    
    # Pre-compute enhanced metrics once
    enhanced, algo = enhance_stocks(stocks)
    
    gainers = [s for s in stocks if s.is_gainer]
    losers = [s for s in stocks if s.is_loser]
    active = sorted(stocks, key=lambda x: x.volume, reverse=True)[:10]
    buy_candidates = [s for s in stocks if s.composite_score >= 50 and s.is_gainer]
    
    market_cache['stocks'] = stocks
    market_cache['enhanced'] = enhanced
    market_cache['algo'] = algo
    market_cache['summary'] = {
        'total': len(stocks),
        'gainers_count': len(gainers),
        'losers_count': len(losers),
        'unchanged_count': len(stocks) - len(gainers) - len(losers),
        'buy_candidates_count': len(buy_candidates)
    }
    market_cache['last_update'] = time.time()
    
    print(f"Market data refreshed. {len(stocks)} stocks analyzed.")


def get_cached_data():
    """Returns cached data, refreshing if stale."""
    if market_cache['stocks'] is None or len(market_cache['stocks']) == 0 or \
       (time.time() - (market_cache['last_update'] or 0)) > CACHE_TTL:
        refresh_market_data()
    return market_cache


@app.route('/')
def index():
    return render_template('dashboard.html')


@app.route('/api/refresh', methods=['POST'])
def api_refresh():
    refresh_market_data()
    return jsonify({'status': 'ok', 'message': 'Data refreshed'})


@app.route('/api/summary')
def api_summary():
    """Returns market summary."""
    data = get_cached_data()
    return jsonify({
        **data['summary'],
        'market_status': get_market_status(),
        'last_update': data['last_update']
    })


from market_hours import get_market_status  # noqa: E402 — placed after Flask setup


@app.route('/api/stocks')
def api_stocks():
    """Get list of stocks for dropdown and main table."""
    data = get_cached_data()
    stocks = []
    
    for s in data['stocks']:
        # Calculate basic valuation metrics
        valuation = financials.calculate_valuation_metrics(s.ticker, s.price)
        
        stocks.append({
            'ticker': s.ticker, 
            'name': s.name, 
            'price': s.price,
            'change': s.change,
            'pe': valuation.get('pe_ratio'),
            'yield': valuation.get('dividend_yield'),
            'sector': valuation.get('sector')
        })
        
    stocks.sort(key=lambda x: x['ticker'])
    return jsonify(stocks)


@app.route('/api/top')
def api_top():
    """Top stocks by composite score with advanced metrics."""
    data = get_cached_data()
    enhanced = data.get('enhanced', [])
    algo = data.get('algo')
    
    if not enhanced or not algo:
        return jsonify([]), 503
    
    limit = request.args.get('limit', 10, type=int)
    
    # Sort by composite score
    sorted_stocks = sorted(enhanced, key=lambda x: x.composite_score, reverse=True)
    
    result = []
    for s in sorted_stocks[:limit]:
        signal_emoji, signal_text, conf = algo.get_signal(s)
        
        base = {
            'ticker': s.ticker,
            'name': s.name,
            'price': s.price,
            'volume': s.volume,
            'change': s.change,
            'change_pct': (s.change / (s.price - s.change) * 100) if s.price and s.change else 0,
            'composite_score': s.composite_score,
            'momentum_score': s.momentum_score,
            'rank': s.rank,
            'sharpe_ratio': s.sharpe_ratio,
            'risk_score': s.risk_score,
            'kelly_fraction': s.kelly_fraction,
            'signal': f"{signal_emoji} {signal_text}",
            'confidence': conf
        }
        result.append(base)
        
    return jsonify(result)


@app.route('/api/gainers')
def api_gainers():
    """Top gainers."""
    data = get_cached_data()
    limit = request.args.get('limit', 10, type=int)
    gainers = sorted([s for s in data['stocks'] if s.is_gainer], 
                     key=lambda x: x.change, reverse=True)
    return jsonify([stock_to_dict(s) for s in gainers[:limit]])


@app.route('/api/losers')
def api_losers():
    """Top losers."""
    data = get_cached_data()
    limit = request.args.get('limit', 10, type=int)
    losers = sorted([s for s in data['stocks'] if s.is_loser], 
                    key=lambda x: x.change)
    return jsonify([stock_to_dict(s) for s in losers[:limit]])


@app.route('/api/active')
def api_active():
    """Most active by volume."""
    data = get_cached_data()
    limit = request.args.get('limit', 10, type=int)
    active = sorted(data['stocks'], key=lambda x: x.volume, reverse=True)
    return jsonify([stock_to_dict(s) for s in active[:limit]])


@app.route('/api/buy_candidates')
def api_buy_candidates():
    """Buy candidates (Smart Risk-Adjusted)."""
    data = get_cached_data()
    enhanced = data.get('enhanced', [])
    algo = data.get('algo')
    
    if not enhanced or not algo:
        return jsonify({'count': 0, 'value': []}), 503
    
    # Filter: Positive Sharpe, Gaining, Reasonable Risk
    candidates = [
        s for s in enhanced 
        if s.sharpe_ratio > 0.1 
        and s.risk_score < 85
        and s.is_gainer
    ]
    
    # Sort by Sharpe Ratio (Risk-Adjusted Return)
    candidates.sort(key=lambda x: x.sharpe_ratio, reverse=True)
    
    result = []
    for s in candidates[:10]:
        signal_emoji, signal_text, conf = algo.get_signal(s)
        result.append({
            'ticker': s.ticker,
            'name': s.name,
            'price': s.price,
            'change': s.change,
            'volume': s.volume,
            'composite_score': s.composite_score,
            'sharpe_ratio': s.sharpe_ratio,
            'risk_score': s.risk_score,
            'signal': f"{signal_emoji} {signal_text}",
            'confidence': conf
        })
        
    return jsonify({
        'count': len(result),
        'value': result
    })


@app.route('/api/alerts')
def api_alerts():
    """Get active market alerts for the ticker tape."""
    data = get_cached_data()
    enhanced = data.get('enhanced', [])
    algo = data.get('algo')
    
    if not enhanced or not algo:
        return jsonify([])
        
    alerts = []
    
    # 1. Bargain Alerts (RSI < 30)
    for s in enhanced:
        signal_emoji, signal_text, conf = algo.get_signal(s)
        
        # Bargain
        if "Bargain" in signal_text or "Oversold" in signal_text:
             alerts.append({
                 'type': 'success',
                 'text': f"💎 {s.ticker}: Bargain Alert! RSI {100 - (100 / (1 + (s.change_pct/100 if s.change_pct else 0))):.0f} (Oversold)" 
             })
             # Note: RSI calc here is a placeholder if not in object, but enhanced should have it.
             # Actually, let's trust the signal text for now.
             
        # Hot Stock
        elif "Overbought" in signal_text:
             alerts.append({
                 'type': 'warning',
                 'text': f"🔥 {s.ticker}: Hot Stock! High RSI (Overbought)"
             })
             
        # Momentum
        elif "Momentum" in signal_text:
             alerts.append({
                 'type': 'info',
                 'text': f"🚀 {s.ticker}: Momentum Building!"
             })
             
    return jsonify(alerts[:10])


@app.route('/api/portfolio/optimize', methods=['POST'])
def optimize_portfolio():
    """Optimize portfolio based on budget using Markowitz Efficient Frontier."""
    try:
        data = request.get_json()
        budget = float(data.get('budget', 100000))
        tickers = data.get('tickers', [])
        
        # If no tickers provided, use top 5 from our 'enhanced' list
        if not tickers:
            cached = get_cached_data()
            if not cached.get('enhanced'):
                # Cache miss? Try one immediate refresh
                refresh_market_data()
                cached = get_cached_data()

            if cached.get('enhanced'):
                # Sort by composite score
                top_stocks = sorted(cached['enhanced'], key=lambda x: x.composite_score, reverse=True)[:5]
                tickers = [s.ticker for s in top_stocks]
        
        if not tickers:
            return jsonify({'error': 'Market data initializing... please wait.'}), 503
            
        # Initialize Optimizer
        optimizer = MLOptimizer()
        result = optimizer.get_optimal_allocation(tickers, budget)
        
        if 'error' in result:
             return jsonify(sanitize_json(result)), 400
             
        return jsonify(sanitize_json(result))
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/stock/<ticker>')
def api_stock(ticker):
    """Get specific stock details."""
    data = get_cached_data()
    enhanced = data.get('enhanced', [])
    algo = data.get('algo')
    
    if not enhanced or not algo:
        return jsonify({'error': 'Data not available'}), 503
    
    for s in enhanced:
        if s.ticker.upper() == ticker.upper():
            signal_emoji, signal_text, conf = algo.get_signal(s)
            
            # Ensure safe values for math
            price = s.price if s.price is not None else 0.0
            change = s.change if s.change is not None else 0.0
            
            # Calculate valuation metrics
            valuation = financials.calculate_valuation_metrics(s.ticker, price)
            
            # Estimate Day Range (since API doesn't provide it)
            # Low = Price - Change (if positive) or Price
            # High = Price + Change (if negative) or Price
            # This is a rough approximation to prevent frontend errors
            day_low = price
            day_high = price
            
            if change > 0:
                day_low = price - change
            elif change < 0:
                day_high = price + abs(change)
            
            # Add some buffer for "range" visual
            day_low = min(day_low, price * 0.98) if price > 0 else 0
            day_high = max(day_high, price * 1.02) if price > 0 else 0

            result = {
                'ticker': s.ticker,
                'name': s.name,
                'price': price,
                'volume': s.volume,
                'change': change,
                'change_pct': s.change_pct if s.change_pct is not None else ((change / (price - change) * 100) if price and change else 0),
                'day_low': day_low,
                'day_high': day_high,
                'valuation': valuation,
                'momentum_score': s.momentum_score,
                'volume_score': s.volume_score,
                'composite_score': s.composite_score,
                'sharpe_ratio': s.sharpe_ratio,
                'risk_score': s.risk_score,
                'kelly_fraction': s.kelly_fraction,
                'signal': f"{signal_emoji} {signal_text}",
                'confidence': conf
            }
            return jsonify(sanitize_json(result))
            
    return jsonify({'error': 'Stock not found'}), 404


@app.route('/datascience')
def datascience():
    """Render Data Science view."""
    top_stocks = get_analyzer().get_top_picks(count=20)
    tickers = [s.ticker for s in top_stocks]
    return render_template('datascience.html', tickers=tickers)

@app.route('/portfolio')
def portfolio_view():
    """Render Portfolio view."""
    return render_template('portfolio.html')

# ============ PORTFOLIO API ============

@app.route('/api/portfolio', methods=['GET'])
def get_portfolio():
    """Get portfolio data."""
    # For now, hardcode user_id='1' or use a default
    # In a real app, use session/auth
    user_id = request.args.get('user_id', '1') 
    portfolio = get_pm().get_portfolio(user_id)
    if not portfolio:
        return jsonify({'holdings': [], 'total_value': 0, 'total_pnl': 0, 'risk_score': 0})
    return jsonify(sanitize_json(portfolio))

@app.route('/api/portfolio/add', methods=['POST'])
def add_trade():
    """Add a trade."""
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'message': 'Request body required'}), 400
        
        ticker = data.get('ticker')
        if not ticker:
            return jsonify({'success': False, 'message': 'ticker is required'}), 400
        
        qty = float(data.get('qty', 0))
        price = float(data.get('price', 0))
        if qty <= 0 or price <= 0:
            return jsonify({'success': False, 'message': 'qty and price must be positive numbers'}), 400
        
        user_id = data.get('user_id', '1')
        success, msg = get_pm().add_trade(user_id, ticker, qty, price)
        return jsonify({'success': success, 'message': msg})
    except (ValueError, TypeError) as e:
        return jsonify({'success': False, 'message': f'Invalid input: {e}'}), 400

@app.route('/api/portfolio/remove', methods=['POST'])
def remove_trade():
    """Remove a trade."""
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'message': 'Request body required'}), 400
        
        ticker = data.get('ticker')
        if not ticker:
            return jsonify({'success': False, 'message': 'ticker is required'}), 400
        
        user_id = data.get('user_id', '1')
        success, msg = get_pm().remove_trade(user_id, ticker)
        return jsonify({'success': success, 'message': msg})
    except (ValueError, TypeError) as e:
        return jsonify({'success': False, 'message': f'Invalid input: {e}'}), 400


@app.route('/api/backtest/<ticker>')
def api_backtest(ticker):
    """Run simulated backtest for a strategy on historical data."""
    strategy = request.args.get('strategy', 'MACD').upper()
    capital = request.args.get('capital', 100000, type=float)
    
    # 1. Get current price for historical calibration
    current_price = 100.0
    stocks = get_cached_data()['stocks']
    for s in stocks:
        if s.ticker.upper() == ticker.upper():
            current_price = s.price
            break
            
    # 2. Get historical data
    df = get_predictor().get_data(ticker, current_price)
    if 'Date' in df.columns:
        df = df.set_index('Date')
        
    print(f"Running {strategy} backtest on {ticker}...")
        
    # 3. Simulate
    bt = Backtester(initial_capital=capital)
    res = bt.run_backtest(df, strategy=strategy)
    
    return jsonify(sanitize_json(res))


@app.route('/api/history/<ticker>')
def api_history(ticker):
    """Get historical data (Real or Simulated)."""
    # Get current price from cache if available for calibration
    current_price = 100.0
    stocks = get_cached_data()['stocks']
    for s in stocks:
        if s.ticker.upper() == ticker.upper():
            current_price = s.price
            break
            
    df = get_predictor().get_data(ticker, current_price)
    
    # Ensure Date is a column and stringified for JSON
    df_clean = df.copy()
    if 'Date' not in df_clean.columns:
        df_clean = df_clean.reset_index()
        
    if 'Date' in df_clean.columns:
        df_clean['Date'] = df_clean['Date'].apply(lambda x: x.isoformat() if hasattr(x, 'isoformat') else str(x))
    
    # Convert to JSON friendly format
    data = df_clean.to_dict(orient='records')
    return jsonify(sanitize_json(data))


@app.route('/api/predict/<ticker>')
def api_predict(ticker):
    """Get ML predictions and trend analysis."""
    # Calibration
    current_price = 100.0
    stocks = get_cached_data()['stocks']
    for s in stocks:
        if s.ticker.upper() == ticker.upper():
            current_price = s.price
            break
            
    df = get_predictor().get_data(ticker, current_price)
    
    trend = get_predictor().analyze_trend(df)
    forecast = get_predictor().predict_next_price(df)
    
    return jsonify(sanitize_json({
        'trend_analysis': trend,
        'price_forecast': forecast
    }))


# ============ NOTIFICATION API ============

@app.route('/api/notifications', methods=['GET'])
def get_notifications():
    """Get recent notifications for the dashboard."""
    return jsonify(notifications_queue[::-1]) # Return newest first

@app.route('/api/notifications', methods=['POST'])
def add_notification():
    """Add a new notification to the queue."""
    try:
        data = request.json
        if not data or 'message' not in data:
            return jsonify({'success': False, 'message': 'Message required'}), 400
        
        notif = {
            'id': int(time.time() * 1000),
            'timestamp': datetime.now().strftime("%H:%M:%S"),
            'message': data['message'],
            'type': data.get('type', 'info') # info, success, warning, error
        }
        
        notifications_queue.append(notif)
        
        # Keep queue size limited
        if len(notifications_queue) > MAX_NOTIFICATIONS:
            notifications_queue.pop(0)
            
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


if __name__ == '__main__':
    print("=" * 50)
    print("  NSE Dashboard Server")
    print("  Powered by TradingView Real-Time Data")
    print("=" * 50)
    print("\nOpen http://127.0.0.1:5001 in your browser.")
    app.run(debug=False, port=5001)
