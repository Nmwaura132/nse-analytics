"""
ML Portfolio Forecast
Runs trend analysis (Linear Regression) and price prediction (Random Forest)
on all 4 portfolio holdings, then sends a Telegram report.
"""
import sys
import os
import requests
from dotenv import load_dotenv
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

from ml_predictor import MLPredictor

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Portfolio: ticker, qty, avg_cost, current_price (from broker), volatility estimate
PORTFOLIO = [
    {'ticker': 'SCOM', 'qty': 19, 'avg_cost': 32.63, 'price': 33.85, 'vol': 0.015},
    {'ticker': 'ABSA', 'qty': 36, 'avg_cost': 29.45, 'price': 29.40, 'vol': 0.012},
    {'ticker': 'KPLC', 'qty': 60, 'avg_cost': 17.79, 'price': 18.35, 'vol': 0.035},
    {'ticker': 'BRIT', 'qty': 20, 'avg_cost': 10.37, 'price': 11.45, 'vol': 0.020},
]


def send_telegram(message):
    if not BOT_TOKEN or not CHAT_ID:
        print("No Telegram creds.")
        return False
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        resp = requests.post(url, json={
            "chat_id": CHAT_ID,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }, timeout=30)
        resp.raise_for_status()
        return True
    except Exception as e:
        print(f"Telegram error: {e}")
        return False


def run_forecast():
    predictor = MLPredictor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    lines = [
        "<b>ML PORTFOLIO FORECAST</b>",
        f"{now}",
        "",
    ]
    
    total_current_value = 0
    total_predicted_value = 0
    total_cost = 0
    
    for stock in PORTFOLIO:
        ticker = stock['ticker']
        qty = stock['qty']
        avg_cost = stock['avg_cost']
        current = stock['price']
        vol = stock['vol']
        
        print(f"\n{'='*50}")
        print(f"Analyzing {ticker}...")
        
        # Generate/load data
        df = predictor.get_data(ticker, current, vol)
        print(f"  Data points: {len(df)}")
        
        # Trend Analysis (Linear Regression)
        trend = predictor.analyze_trend(df)
        trend_emoji = {"Upward": "📈", "Downward": "📉", "Neutral": "➡️"}.get(trend['trend'], "❓")
        print(f"  Trend: {trend['trend']} (slope={trend['slope']:.4f}, R2={trend['r2']:.2f})")
        
        # Price Prediction (Random Forest)
        forecast = predictor.predict_next_price(df)
        
        if 'error' in forecast:
            print(f"  Prediction: {forecast['error']}")
            predicted = current
            change_pct = 0
        else:
            predicted = forecast['predicted_price']
            change_pct = forecast['change_forecast'] * 100
            mse = forecast['mse']
            print(f"  Last Close: {forecast['last_close']:.2f}")
            print(f"  Predicted: {predicted:.2f} ({change_pct:+.2f}%)")
            print(f"  MSE: {mse:.4f}")
        
        # Portfolio impact
        current_value = qty * current
        predicted_value = qty * predicted
        cost_basis = qty * avg_cost
        current_pnl = current_value - cost_basis
        predicted_pnl = predicted_value - cost_basis
        
        total_current_value += current_value
        total_predicted_value += predicted_value
        total_cost += cost_basis
        
        # Signal
        if change_pct > 1:
            signal = "BUY / HOLD"
            signal_emoji = "🟢"
        elif change_pct < -1:
            signal = "CAUTION"
            signal_emoji = "🔴"
        else:
            signal = "HOLD"
            signal_emoji = "🟡"
        
        # Confidence based on R2
        r2 = trend['r2']
        if r2 > 0.7:
            confidence = "High"
        elif r2 > 0.4:
            confidence = "Medium"
        else:
            confidence = "Low"
        
        lines.append(f"{trend_emoji} <b>{ticker}</b> ({qty} shares)")
        lines.append(f"  Now: {current:.2f} | Predicted: <b>{predicted:.2f}</b> ({change_pct:+.1f}%)")
        lines.append(f"  Trend: {trend['trend']} | Confidence: {confidence} (R2={r2:.2f})")
        lines.append(f"  Signal: {signal_emoji} {signal}")
        lines.append(f"  P/L if predicted: KES {predicted_pnl:+,.0f}")
        lines.append("")
    
    # Summary
    total_current_pnl = total_current_value - total_cost
    total_predicted_pnl = total_predicted_value - total_cost
    current_pct = (total_current_pnl / total_cost * 100) if total_cost > 0 else 0
    predicted_pct = (total_predicted_pnl / total_cost * 100) if total_cost > 0 else 0
    
    lines.append("<b>PORTFOLIO SUMMARY</b>")
    lines.append(f"Cost Basis: KES {total_cost:,.0f}")
    lines.append(f"Current Value: KES {total_current_value:,.0f} ({current_pct:+.1f}%)")
    lines.append(f"<b>ML Predicted: KES {total_predicted_value:,.0f} ({predicted_pct:+.1f}%)</b>")
    lines.append("")
    lines.append("<i>Note: Predictions use simulated 6-month history (GBM) + Random Forest. Not financial advice.</i>")
    
    message = "\n".join(lines)
    print(f"\n{'='*50}")
    print("TELEGRAM MESSAGE:")
    print(message)
    
    # Send
    success = send_telegram(message)
    print(f"\nTelegram sent: {success}")


if __name__ == "__main__":
    run_forecast()
