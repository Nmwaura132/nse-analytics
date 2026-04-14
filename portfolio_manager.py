from sqlalchemy.orm import Session
from database import PortfolioItem, SessionLocal
from comprehensive_analyzer import ComprehensiveAnalyzer, StockScore
from advanced_algorithms import AdvancedPortfolioAlgorithms, enhance_stocks
import logging

logger = logging.getLogger(__name__)

class PortfolioManager:
    def __init__(self):
        self.analyzer = ComprehensiveAnalyzer()
        self.algo = None
        self.last_alerts = {}  # Cache for alert throttling (user_id -> type -> timestamp)
        
    def get_db(self):
        return SessionLocal()

    def add_trade(self, user_id: str, ticker: str, qty: float, price: float):
        """Add a trade to the portfolio."""
        db = self.get_db()
        try:
            # Check if stock exists in current holdings
            item = db.query(PortfolioItem).filter_by(user_id=str(user_id), ticker=ticker.upper()).first()
            
            if item:
                # Update existing position (Weighted Average Cost)
                total_cost = (item.quantity * item.avg_cost) + (qty * price)
                total_qty = item.quantity + qty
                item.avg_cost = total_cost / total_qty
                item.quantity = total_qty
            else:
                # Create new position
                item = PortfolioItem(
                    user_id=str(user_id),
                    ticker=ticker.upper(),
                    quantity=qty,
                    avg_cost=price
                )
                db.add(item)
            
            db.commit()
            return True, f"✅ Tracked: {qty} shares of {ticker.upper()} @ {price:.2f}"
        except Exception as e:
            db.rollback()
            logger.error(f"Error adding trade: {e}")
            return False, f"❌ Error: {str(e)}"
        finally:
            db.close()

    def remove_trade(self, user_id: str, ticker: str):
        """Remove a trade from the portfolio."""
        db = self.get_db()
        try:
            item = db.query(PortfolioItem).filter_by(user_id=str(user_id), ticker=ticker.upper()).first()
            if item:
                db.delete(item)
                db.commit()
                return True, f"✅ Removed {ticker.upper()} from portfolio."
            else:
                return False, f"❌ Stock {ticker.upper()} not found in portfolio."
        except Exception as e:
            db.rollback()
            logger.error(f"Error removing trade: {e}")
            return False, f"❌ Error: {str(e)}"
        finally:
            db.close()

    def get_portfolio(self, user_id: str):
        """Get current portfolio status with real-time data."""
        db = self.get_db()
        try:
            items = db.query(PortfolioItem).filter_by(user_id=str(user_id)).all()
            if not items:
                return None
            
            # Fetch real-time data
            stocks = []
            try:
                stocks = self.analyzer.analyze_all_stocks()
            except Exception as e:
                logger.error(f"Failed to fetch live data: {e}")
                
            # Create a map, fallback to empty if failed
            stock_map = {}
            if stocks:
                enhanced_stocks, _ = enhance_stocks(stocks)
                stock_map = {s.ticker: s for s in enhanced_stocks}
            
            portfolio_data = []
            total_value = 0
            total_cost = 0
            
            for item in items:
                current_stock = stock_map.get(item.ticker)
                
                # PRICE LOGIC
                current_price = 0.0
                
                # 1. IPO Special Case: KPC
                if item.ticker == 'KPC':
                    current_price = 9.00 # Fixed IPO Price
                    
                # 2. Live Data Available
                elif current_stock:
                    current_price = current_stock.price
                    
                # 3. Fallback (Offline/Error): Use Cost Basis to avoid scary -100% PnL
                else:
                    current_price = item.avg_cost 
                
                value = item.quantity * current_price
                cost = item.quantity * item.avg_cost
                pnl = value - cost
                pnl_pct = (pnl / cost * 100) if cost > 0 else 0
                
                # Risk Data
                risk_score = current_stock.risk_score if current_stock else 50
                sharpe = current_stock.sharpe_ratio if current_stock else 0
                
                portfolio_data.append({
                    'ticker': item.ticker,
                    'qty': item.quantity,
                    'avg_cost': item.avg_cost,
                    'current_price': current_price,
                    'value': value,
                    'pnl': pnl,
                    'pnl_pct': pnl_pct,
                    'risk_score': risk_score,
                    'sharpe': sharpe,
                    'is_live': bool(current_stock) or item.ticker == 'KPC'
                })
                
                total_value += value
                total_cost += cost
                
            # Calculate Portfolio Risk Score (Weighted Average)
            portfolio_risk = 0
            if total_value > 0:
                for p in portfolio_data:
                    weight = p['value'] / total_value
                    portfolio_risk += p['risk_score'] * weight
            
            return {
                'holdings': portfolio_data,
                'total_value': total_value,
                'total_cost': total_cost,
                'total_pnl': total_value - total_cost,
                'total_pnl_pct': ((total_value - total_cost) / total_cost * 100) if total_cost > 0 else 0,
                'risk_score': portfolio_risk,
                'is_offline': not stocks
            }
            
        finally:
            db.close()

    def check_alerts(self, user_id: str):
        """Check for risk alerts with throttling (Portfolio + Market)."""
        import time

        alerts = []
        now = time.time()

        # Initialize throttle cache for user
        if user_id not in self.last_alerts:
            self.last_alerts[user_id] = {}

        # --- PORTFOLIO ALERTS ---
        port = self.get_portfolio(user_id)
        if port:
            # 1. High Portfolio Risk (Throttle: 1 day)
            if port['risk_score'] > 75:
                last_time = self.last_alerts[user_id].get('risk_high', 0)
                if now - last_time > 86400:
                    alerts.append(f"⚠️ **High Risk Alert:** Portfolio Risk Score is {port['risk_score']:.0f}/100. Consider rebalancing.")
                    self.last_alerts[user_id]['risk_high'] = now

            # 2. Portfolio Stock Analysis (Throttle: 10 mins)
            for item in port['holdings']:
                alert_key = f"port_{item['ticker']}"
                last_time = self.last_alerts[user_id].get(alert_key, 0)

                is_stop_loss = item['pnl_pct'] < -10
                is_volatile  = abs(item['pnl_pct']) >= 2.0

                if (is_stop_loss or is_volatile) and (now - last_time > 600):
                    reason = "🚨 STOP-LOSS" if is_stop_loss else "🔔 PORTFOLIO MOVE"
                    alerts.append(f"{reason}: {item['ticker']} is at {item['pnl_pct']:.1f}% (Price: {item['current_price']})")
                    self.last_alerts[user_id][alert_key] = now

        # --- MARKET ALERTS ---
        # analyze_all_stocks() is cheap when the bot-level TTL cache is warm
        # (get_cached_stocks() returns in microseconds). We always call it once
        # here rather than duplicating caching logic in portfolio_manager.
        stocks = self.analyzer.analyze_all_stocks()
        for s in stocks:
            move_alert  = False
            smart_alert = False
            msg = ""

            # 1. Price Moves ≥5 %
            if s.change_pct and abs(s.change_pct) >= 5.0:
                direction = "🚀 SURGING" if s.change_pct > 0 else "🔻 CRASHING"
                msg = f"{direction}: **{s.ticker}** is moving! {s.change_pct:+.1f}% (Price: {s.price})"
                move_alert = True

            # 2. Smart Signals — Oversold (<20) or Overbought (>80) momentum
            elif s.momentum_score < 20:
                msg = f"💎 **BARGAIN ALERT:** {s.ticker} is very cheap right now! (Momentum: {s.momentum_score:.0f})"
                smart_alert = True
            elif s.momentum_score > 80:
                msg = f"🔥 **HOT STOCK:** {s.ticker} prices have surged. Consider taking profits? (Momentum: {s.momentum_score:.0f})"
                smart_alert = True

            if move_alert or smart_alert:
                alert_key = f"market_{s.ticker}_{'smart' if smart_alert else 'move'}"
                last_time  = self.last_alerts[user_id].get(alert_key, 0)
                throttle   = 14400 if smart_alert else 7200

                if now - last_time > throttle:
                    alerts.append(msg)
                    self.last_alerts[user_id][alert_key] = now

        return alerts
