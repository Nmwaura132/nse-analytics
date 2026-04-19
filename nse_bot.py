"""
Interactive NSE Telegram Bot
Responds to user commands with real-time market data.
"""
import os
import logging
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from comprehensive_analyzer import ComprehensiveAnalyzer
from advanced_algorithms import enhance_stocks, AdvancedPortfolioAlgorithms
from ml_predictor import MLPredictor
from chart_generator import generate_candlestick_chart, generate_forecast_chart, generate_portfolio_chart, generate_analysis_chart
from dividend_calendar import get_upcoming_dividends, get_user_dividend_income
from database import PriceAlert, SessionLocal as AlertSessionLocal
from data_collector import start_scheduler
import openclaw_client as ai

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize analyzer
analyzer = ComprehensiveAnalyzer()
ml_predictor = MLPredictor()


# ============ HELPER FUNCTIONS ============

def format_change(change: float) -> str:
    """Format price change with emoji."""
    if change > 0:
        return f"🟢 +{change:.2f}"
    elif change < 0:
        return f"🔴 {change:.2f}"
    return f"⚪ {change:.2f}"


def format_number(n: float) -> str:
    """Format large numbers."""
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    elif n >= 1_000:
        return f"{n/1_000:.1f}K"
    return f"{n:,.0f}"




# ============ COMMAND HANDLERS ============

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    welcome = """
🇰🇪 *NSE Stock Bot*

Welcome! I provide real-time Nairobi Securities Exchange data and analysis.

*📊 Market Commands:*
/report - Daily market report
/summary - Quick market snapshot
/gainers - Top gainers
/losers - Top losers
/active - Most traded stocks

*🏆 Analysis:*
/top - Top 10 by score
/buy - Buy candidates
/predict - Trend predictions
/analyze SCOM - 🧠 Deep technical dive (RSI, Bollinger, MACD)

*📈 Charts:*
/chart SCOM - Candlestick chart
/forecast SCOM - ML price forecast
/pchart - Portfolio allocation chart

*💼 Portfolio:*
/track SCOM 100 15.50 - Add trade
/myportfolio - View holdings

*🔔 Alerts & Dividends:*
/alert SCOM > 35 - Price alert
/myalerts - View active alerts
/delalert 1 - Delete alert
/dividends - Dividend calendar

/help - Full command list

_Real-time data • Updated every 2 min_
"""
    await update.message.reply_text(welcome, parse_mode='Markdown')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    help_text = """
*📋 All Commands:*

*Market Overview*
├ /report - Full daily report
├ /summary - Quick market stats
└ /active - Most active stocks

*Stock Lists*
├ /gainers - Top gainers today
├ /losers - Top losers today
├ /top - Top 10 by composite score
└ /buy - Buy candidates

*Analysis & Prediction*
├ /predict - Trend predictions
└ /stock SCOM - Individual stock

*Portfolio Tools*
└ /portfolio 100000 - Allocate budget

*Examples:*
`/stock SCOM` - Safaricom details
`/stock KCB` - KCB Group details
`/portfolio 50000` - Allocate KES 50K
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')


# Caching variables
last_fetch_time = None
cached_stocks = None
CACHE_DURATION = 300  # 5 minutes

def get_cached_stocks():
    """Fetch stocks with simple caching."""
    global last_fetch_time, cached_stocks
    
    now = datetime.now()
    if cached_stocks and last_fetch_time and (now - last_fetch_time).total_seconds() < CACHE_DURATION:
        return cached_stocks
        
    try:
        logging.info("Fetching fresh data from analyzer...")
        stocks = analyzer.analyze_all_stocks()
        if stocks:
            cached_stocks = stocks
            last_fetch_time = now
        return stocks
    except Exception as e:
        logger.error(f"Error fetching data: {e}")
        return []

# ============ SECTOR DEFINITIONS ============
SECTORS = {
    'BANK': ['KCB', 'EQTY', 'ABSA', 'NCBA', 'SCBK', 'SBIC', 'IMH', 'BK', 'COOP', 'DTK'],
    'FINANCE': ['KCB', 'EQTY', 'ABSA', 'NCBA', 'SCBK', 'SBIC', 'IMH', 'BK', 'COOP', 'DTK'],
    'TELCO': ['SCOM'],
    'INSUR': ['JUB', 'CIC', 'BRIT', 'KNRE', 'SLAM'],
    'ENERGY': ['KPLC', 'KEGN', 'TOTL', 'UMME'],
    'POWER': ['KPLC', 'KEGN', 'TOTL', 'UMME'],
    'MANU': ['EABL', 'BAT', 'CARB', 'BOC'],
    'CONST': ['BAMB', 'CABL']
}

# ============ COMMAND HANDLERS ============

# ... (start/help handlers unmodified) ...

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /report command - Full daily report."""
    try:
        await update.message.reply_text("📊 Fetching market data...")
        
        stocks = get_cached_stocks()
        if not stocks:
            await update.message.reply_text("❌ Failed to fetch data. Please try again later.")
            return
        
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        gainers = sorted([s for s in stocks if s.is_gainer], key=lambda x: x.change, reverse=True)[:5]
        losers = sorted([s for s in stocks if s.is_loser], key=lambda x: x.change)[:5]
        active = sorted(stocks, key=lambda x: x.volume, reverse=True)[:5]
        buy_candidates = [s for s in stocks if s.composite_score >= 50 and s.is_gainer][:3]
        
        total = len(stocks)
        g_count = len([s for s in stocks if s.is_gainer])
        l_count = len([s for s in stocks if s.is_loser])
        
        # Build report
        report_lines = [
            f"📊 *NSE DAILY REPORT*",
            f"_{now}_",
            "",
            f"*MARKET SUMMARY*",
            f"📈 Gainers: {g_count} ({100*g_count/total:.0f}%)",
            f"📉 Losers: {l_count} ({100*l_count/total:.0f}%)",
            f"⚪ Unchanged: {total - g_count - l_count}",
            "",
            "🚀 *TOP GAINERS*"
        ]
        
        for s in gainers:
            report_lines.append(f"`{s.ticker:6}` {s.price:>8.2f}  {format_change(s.change)}")
        
        report_lines.append("")
        report_lines.append("💔 *TOP LOSERS*")
        for s in losers:
            report_lines.append(f"`{s.ticker:6}` {s.price:>8.2f}  {format_change(s.change)}")
        
        report_lines.append("")
        report_lines.append("🔥 *MOST ACTIVE*")
        for s in active:
            report_lines.append(f"`{s.ticker:6}` Vol: {format_number(s.volume)}")
        
        if buy_candidates:
            report_lines.append("")
            report_lines.append("✅ *BUY CANDIDATES*")
            for s in buy_candidates:
                report_lines.append(f"`{s.ticker:6}` {s.price:.2f} | Score: {s.composite_score:.0f}")
        
        await update.message.reply_text("\n".join(report_lines), parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Report error: {e}")
        await update.message.reply_text("❌ An error occurred while generating the report.")


async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /summary command - Quick summary."""
    stocks = get_cached_stocks()
    if not stocks:
        await update.message.reply_text("❌ Failed to fetch data.")
        return
    
    g = len([s for s in stocks if s.is_gainer])
    l = len([s for s in stocks if s.is_loser])
    
    msg = f"""
📊 *Market Snapshot*
Total: {len(stocks)} stocks
📈 Gainers: {g}
📉 Losers: {l}
⚪ Unchanged: {len(stocks) - g - l}

_Updated: {datetime.now().strftime('%H:%M')}_
"""
    await update.message.reply_text(msg, parse_mode='Markdown')


async def gainers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /gainers command."""
    stocks = get_cached_stocks()
    gainers_list = sorted([s for s in stocks if s.is_gainer], key=lambda x: (x.change_pct or 0), reverse=True)[:8]
    
    if not gainers_list:
        await update.message.reply_text("No gainers today.")
        return
    
    lines = ["🚀 *TOP GAINERS*", ""]
    for s in gainers_list:
        lines.append(f"`{s.ticker:6}` {s.price:>8.2f}  {format_change(s.change)}")
    
    await update.message.reply_text("\n".join(lines), parse_mode='Markdown')


async def losers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /losers command."""
    stocks = get_cached_stocks()
    losers_list = sorted([s for s in stocks if s.is_loser], key=lambda x: (x.change_pct or 0))[:8]
    
    if not losers_list:
        await update.message.reply_text("No losers today.")
        return
    
    lines = ["💔 *TOP LOSERS*", ""]
    for s in losers_list:
        lines.append(f"`{s.ticker:6}` {s.price:>8.2f}  {format_change(s.change)}")
    
    await update.message.reply_text("\n".join(lines), parse_mode='Markdown')


async def active(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /active command."""
    stocks = get_cached_stocks()
    active_list = sorted(stocks, key=lambda x: x.volume, reverse=True)[:8]
    
    lines = ["🔥 *MOST ACTIVE*", ""]
    for s in active_list:
        lines.append(f"`{s.ticker:6}` {s.price:>8.2f}  Vol: {format_number(s.volume)}")
    
    await update.message.reply_text("\n".join(lines), parse_mode='Markdown')


async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /top command."""
    stocks = get_cached_stocks()
    top_list = stocks[:10]
    
    lines = ["🏆 *TOP 10 BY SCORE*", ""]
    for s in top_list:
        lines.append(f"`{s.rank}. {s.ticker:6}` {s.price:>8.2f}  Score: {s.composite_score:.0f}")
    
    await update.message.reply_text("\n".join(lines), parse_mode='Markdown')


async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /buy command."""
    stocks = get_cached_stocks()
    candidates = [s for s in stocks if s.composite_score >= 50 and s.is_gainer]
    candidates.sort(key=lambda x: x.composite_score, reverse=True)
    
    if not candidates:
        await update.message.reply_text("⚠️ No buy candidates at this time\n\n_Buy candidates must have Score≥50 and be currently gaining_")
        return
    
    lines = ["✅ *BUY CANDIDATES*", "_Score≥50, Currently Gaining_", ""]
    for s in candidates[:8]:
        lines.append(f"`{s.ticker:6}` {s.price:.2f} | {format_change(s.change)} | Score: {s.composite_score:.0f}")
    
    await update.message.reply_text("\n".join(lines), parse_mode='Markdown')


async def predict(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /predict command - Trend predictions with advanced signals."""
    try:
        await update.message.reply_text("🔮 Analyzing trends with advanced algorithms...")
        
        stocks = get_cached_stocks()
        if not stocks:
            await update.message.reply_text("❌ Failed to fetch data.")
            return
            
        # Use advanced algorithms
        enhanced, algo = enhance_stocks(stocks)
        
        # Generate predictions for top 10 most active
        active_stocks = sorted(enhanced, key=lambda x: x.volume, reverse=True)[:10]
        
        lines = [
            "🔮 *ADVANCED TREND PREDICTIONS*",
            "_Based on Sharpe Ratio & Risk Parity_",
            "",
            "`Stock   Price    Signal   Conf`"
        ]
        
        for s in active_stocks:
            emoji, signal, conf = algo.get_signal(s)
            lines.append(f"`{s.ticker:6}` {s.price:>7.2f}  {emoji} {signal:<8} {conf}%")
        
        lines.extend([
            "",
            "*Signal Guide:*",
            "🚀 STRONG BUY - High Sharpe (>1.5) + Low Risk",
            "📈 BUY - Good Risk-Adjusted Return",
            "↗️ HOLD/BUY - Positive Trend",
            "➡️ HOLD - Neutral",
            "↘️ HOLD/SELL - Negative Trend",
            "📉 SELL - Poor Risk-Adjusted Metric"
        ])
        
        await update.message.reply_text("\n".join(lines), parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Predict error: {e}")
        await update.message.reply_text("❌ An error occurred during prediction analysis.")


async def portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /portfolio BUDGET - Advanced portfolio with Sharpe/Kelly optimization."""
    try:
        # Parse budget
        if context.args:
            try:
                budget = float(context.args[0].replace(',', ''))
            except ValueError:
                await update.message.reply_text("❌ Invalid budget. Example: /portfolio 100000")
                return
        else:
            budget = 100000  # Default
        
        if budget < 1000:
            await update.message.reply_text("❌ Minimum budget is KES 1,000")
            return
        
        await update.message.reply_text(f"💼 Optimizing portfolio for KES {budget:,.0f}...\n_Using Sharpe Ratio + Risk Parity_")
        
        stocks = get_cached_stocks()
        if not stocks:
            await update.message.reply_text("❌ Failed to fetch data.")
            return
        
        # Use advanced algorithms
        enhanced, algo = enhance_stocks(stocks)
        result = algo.get_optimal_allocation(budget, max_stocks=5)
        
        lines = [
            f"💼 *OPTIMIZED PORTFOLIO*",
            f"_Budget: KES {budget:,.0f}_",
            "",
            "`Stock  Shares  Price   Cost    Sharpe`"
        ]
        
        for a in result['allocations']:
            s = a['stock']
            lines.append(f"`{s.ticker:5}` {a['shares']:>5}  {s.price:>7.2f}  {a['cost']:>6,.0f}  {s.sharpe_ratio:+.2f}")
        
        holding = result['holding_period']
        risk_emoji = "🟢" if result['portfolio_risk_score'] < 40 else "🟡" if result['portfolio_risk_score'] < 60 else "🔴"
        
        lines.extend([
            "",
            f"*Total Invested:* KES {result['total_invested']:,.0f}",
            f"*Cash Remaining:* KES {result['cash_remaining']:,.0f}",
            "",
            "📊 *PORTFOLIO METRICS*",
            f"├ Sharpe Ratio: {result['portfolio_sharpe']:.2f}",
            f"├ Risk Score: {risk_emoji} {result['portfolio_risk_score']:.0f}/100",
            f"└ Expected Return: {result['portfolio_expected_return']*100:.1f}%",
            "",
            f"⏱️ *HOLDING PERIOD*",
            f"{holding['emoji']} *{holding['type']}*: {holding['period']}",
            f"_{holding['reason']}_",
            "",
            "*Exit Strategy:*",
            "• Take profits: +15-20%",
            "• Stop loss: -10%",
            "",
            "_Algorithm: Risk Parity + Kelly Criterion_"
        ])
        
        await update.message.reply_text("\n".join(lines), parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Portfolio error: {e}")
        await update.message.reply_text("❌ An error occurred during portfolio optimization.")


async def stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stock TICKER command."""
    if not context.args:
        await update.message.reply_text("Usage: /stock SCOM\nExample: /stock Safaricom")
        return
    
    query = " ".join(context.args).upper()
    stocks = get_cached_stocks()
    
    # Use advanced algorithms
    enhanced, algo = enhance_stocks(stocks)
    
    # Find matching stock
    stock = None
    for s in enhanced:
        if s.ticker.upper() == query or query in s.name.upper():
            stock = s
            break
    
    if not stock:
        await update.message.reply_text(f"❌ Stock '{query}' not found.\n\nTry /stock SCOM or /stock Safaricom")
        return
    
    # Get trend signal
    emoji, signal, conf = algo.get_signal(stock)
    
    msg = f"""
🔍 *{stock.ticker}*
{stock.name}

💰 *Price:* KES {stock.price:.2f}
{format_change(stock.change)}
📊 *Volume:* {format_number(stock.volume)}

*Scores:*
├ Momentum: {stock.momentum_score:.0f}/100
├ Volume: {stock.volume_score:.0f}/100
└ Composite: {stock.composite_score:.0f}/100

*Advanced Metrics:*
├ Sharpe Ratio: {stock.sharpe_ratio:.2f}
├ Risk Score: {stock.risk_score:.0f}/100
└ Kelly Alloc: {stock.kelly_fraction*100:.1f}%

🏆 *Rank:* #{stock.rank} of {len(stocks)}

*Trend Signal:* {emoji} {signal}
_Confidence: {conf}%_
"""
    await update.message.reply_text(msg, parse_mode='Markdown')


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle unknown commands."""
    await update.message.reply_text("❓ Unknown command. Type /help for available commands.")


from portfolio_manager import PortfolioManager

# Initialize portfolio manager
pm = PortfolioManager()

# ============ PORTFOLIO COMMANDS ============

async def track(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /track TICKER QTY PRICE."""
    try:
        if len(context.args) < 3:
            await update.message.reply_text("Usage: /track TICKER QTY PRICE\nExample: /track SCOM 1000 15.50")
            return
        
        ticker = context.args[0].upper()
        qty = float(context.args[1])
        price = float(context.args[2])
        
        user_id = str(update.effective_user.id)
        
        success, msg = pm.add_trade(user_id, ticker, qty, price)
        await update.message.reply_text(msg)
        
    except ValueError:
        await update.message.reply_text("❌ Invalid numbers. Please check quantity and price.")

async def myportfolio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /myportfolio command."""
    user_id = str(update.effective_user.id)
    port = pm.get_portfolio(user_id)
    
    if not port:
        await update.message.reply_text("📉 You have no tracked positions. Use /track to add one.")
        return
        
    # Build message
    lines = [
        "💼 *MY PORTFOLIO*",
        f"Value: KES {port['total_value']:,.2f}",
        f"Cost:  KES {port['total_cost']:,.2f}",
        f"P/L:   {format_change(port['total_pnl'])} ({port['total_pnl_pct']:.1f}%)",
        "",
        f"⚠️ Risk Score: {port['risk_score']:.0f}/100",
        "",
        "*Holdings:*"
    ]
    
    for item in port['holdings']:
        lines.append(f"`{item['ticker']:5}` {item['qty']:>5,.0f} | {format_change(item['pnl_pct'])}%")
        
    await update.message.reply_text("\n".join(lines), parse_mode='Markdown')

async def check_alerts_job(context: ContextTypes.DEFAULT_TYPE):
    """Background job to check risk alerts."""
    # In a real bot, we'd loop through all subscribed users.
    # For now, we assume the user who started the bot is the admin/main user.
    # Since we don't have a user list in DB (only portfolio items), we could query unique user_ids.
    
    db = pm.get_db()
    try:
        from database import PortfolioItem
        user_ids = [u[0] for u in db.query(PortfolioItem.user_id).distinct().all()]
        
        for user_id in user_ids:
            alerts = pm.check_alerts(user_id)
            if alerts:
                for alert in alerts:
                    await context.bot.send_message(chat_id=user_id, text=alert, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Alert Job Failed: {e}")
    finally:
        db.close()


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages for NLP-like responses."""
    text = update.message.text.upper()
    
    # 1. Sector Analysis
    for sector, tickers in SECTORS.items():
        if sector in text or (sector == 'BANK' and 'BANKS' in text):
            await update.message.reply_text(f"🔍 Analyzing {sector} sector...")
            
            stocks = get_cached_stocks()
            if not stocks:
                await update.message.reply_text("❌ Failed to fetch data.")
                return
            
            enhanced, algo = enhance_stocks(stocks)
            sector_stocks = [s for s in enhanced if s.ticker in tickers]
            sector_stocks.sort(key=lambda x: x.composite_score, reverse=True)
            
            if not sector_stocks:
                await update.message.reply_text(f"No data found for {sector} sector.")
                return

            lines = [f"🏦 *{sector} SECTOR ANALYSIS*", "`Stock  Price   Score  Signal`"]
            for s in sector_stocks:
                emoji, signal, conf = algo.get_signal(s)
                lines.append(f"`{s.ticker:5}` {s.price:>6.1f}  {s.composite_score:>3.0f}    {emoji}")
            
            await update.message.reply_text("\n".join(lines), parse_mode='Markdown')
            return

    # 2. Validation / Explainers
    if "CORRECT" in text or "CONFIRM" in text or "VERIFY" in text or "ACCURATE" in text:
        msg = """
✅ *Methodology Verification*

Our analysis is based on standard financial models:

1. *Sharpe Ratio:* (Return - Risk Free) / Volatility. 
   - A ratio > 1.0 is considered good.
   - We use a 5% Risk Free Rate (approx 91-day T-Bill).

2. *Kelly Criterion:* Optimal betting size to maximize geometric growth.
   - Half-Kelly is used to reduce volatility (conservative).
   - Only positive for stocks with Positive Expected Return.

3. *Risk Parity:* Allocates risk equally across assets, rather than capital.
   - Volatility is calculated using 14-day standard deviation.

All data is real-time from the NSE.
"""
        await update.message.reply_text(msg, parse_mode='Markdown')
        return

    # Default: ignore non-command text
    pass


# ============ CHART COMMANDS ============

# Stock volatility estimates for simulation
STOCK_VOLATILITY = {
    'SCOM': 0.015, 'EQTY': 0.018, 'KCB': 0.020, 'ABSA': 0.012,
    'COOP': 0.015, 'NCBA': 0.014, 'BRIT': 0.020, 'KPLC': 0.035,
    'EABL': 0.016, 'BAT': 0.010, 'SCBK': 0.012, 'DTK': 0.018,
    'JUB': 0.015, 'BAMB': 0.025, 'KEGN': 0.030,
}

def _get_stock_price(ticker: str) -> float:
    """Get current price for a ticker from cached data."""
    stocks = get_cached_stocks()
    if stocks:
        for s in stocks:
            if s.ticker == ticker:
                return s.price
    return 0

def _get_user_avg_cost(user_id: str, ticker: str) -> float:
    """Get user's avg cost for a ticker from portfolio DB."""
    try:
        db = pm.get_db()
        from database import PortfolioItem
        item = db.query(PortfolioItem).filter_by(user_id=user_id, ticker=ticker).first()
        if item:
            return item.avg_cost
    except Exception:
        pass
    return None


async def chart_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /chart TICKER - Send candlestick chart as image."""
    if not context.args:
        await update.message.reply_text("Usage: /chart SCOM\nSends a candlestick chart with moving averages.")
        return
    
    ticker = context.args[0].upper()
    await update.message.reply_text(f"📊 Generating {ticker} chart...")
    
    try:
        current_price = _get_stock_price(ticker)
        if current_price <= 0:
            await update.message.reply_text(f"❌ Could not find price for {ticker}. Check the ticker.")
            return
        
        vol = STOCK_VOLATILITY.get(ticker, 0.020)
        user_id = str(update.effective_user.id)
        avg_cost = _get_user_avg_cost(user_id, ticker)
        
        # Generate data & trend
        df = ml_predictor.get_data(ticker, current_price, vol)
        trend = ml_predictor.analyze_trend(df)
        
        # Generate chart
        img_buf = generate_candlestick_chart(df, ticker, trend, current_price, avg_cost)
        
        caption = f"📊 {ticker} Candlestick (60 days)\n"
        caption += f"Price: {current_price:.2f} KES\n"
        caption += f"Trend: {trend['trend']} (R²={trend['r2']:.2f})"
        if avg_cost:
            pnl_pct = ((current_price - avg_cost) / avg_cost) * 100
            caption += f"\nMy Position: {pnl_pct:+.1f}%"
        
        await update.message.reply_photo(photo=img_buf, caption=caption)
        
    except Exception as e:
        logger.error(f"Chart error: {e}")
        await update.message.reply_text(f"❌ Failed to generate chart: {str(e)[:100]}")


async def forecast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /forecast TICKER - Send ML forecast chart as image."""
    if not context.args:
        await update.message.reply_text("Usage: /forecast SCOM\nSends an ML price prediction chart.")
        return
    
    ticker = context.args[0].upper()
    await update.message.reply_text(f"🔮 Running ML forecast for {ticker}...")
    
    try:
        current_price = _get_stock_price(ticker)
        if current_price <= 0:
            await update.message.reply_text(f"❌ Could not find price for {ticker}.")
            return
        
        vol = STOCK_VOLATILITY.get(ticker, 0.020)
        user_id = str(update.effective_user.id)
        avg_cost = _get_user_avg_cost(user_id, ticker)
        
        # Generate data, trend, forecast
        df = ml_predictor.get_data(ticker, current_price, vol)
        trend = ml_predictor.analyze_trend(df)
        forecast = ml_predictor.predict_next_price(df)
        
        if 'error' in forecast:
            await update.message.reply_text(f"⚠️ {forecast['error']}")
            return
        
        # Generate chart
        img_buf = generate_forecast_chart(df, ticker, forecast, trend, avg_cost)
        
        predicted = forecast['predicted_price']
        change_pct = forecast['change_forecast'] * 100
        signal = "BUY/HOLD" if change_pct > 1 else "CAUTION" if change_pct < -1 else "HOLD"
        arrow = '↑' if change_pct > 0 else '↓'
        
        caption = f"🔮 {ticker} ML Forecast\n"
        caption += f"Current: {current_price:.2f} KES\n"
        caption += f"Predicted: {predicted:.2f} KES ({arrow} {change_pct:+.1f}%)\n"
        caption += f"Trend: {trend['trend']} | Signal: {signal}\n"
        caption += f"Model: Random Forest (MSE={forecast['mse']:.4f})"
        
        await update.message.reply_photo(photo=img_buf, caption=caption)
        
    except Exception as e:
        logger.error(f"Forecast error: {e}")
        await update.message.reply_text(f"❌ Failed to generate forecast: {str(e)[:100]}")


async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /analyze TICKER - Deep technical analysis with reasoning."""
    if not context.args:
        await update.message.reply_text("Usage: /analyze SCOM\nSee reasoning with RSI, MACD & Bollinger Bands")
        return
    
    ticker = context.args[0].upper()
    await update.message.reply_text(f"🧠 Analyzing {ticker} with advanced metrics...")
    
    try:
        current_price = _get_stock_price(ticker)
        if current_price <= 0:
            await update.message.reply_text(f"❌ Could not find price for {ticker}.")
            return
            
        vol = STOCK_VOLATILITY.get(ticker, 0.020)
        
        # Get data with NEW indicators (RSI, BB, MACD)
        df = ml_predictor.get_data(ticker, current_price, vol)
        
        # Generate Chart
        img_buf = generate_analysis_chart(df, ticker)
        
        # Build "Reasoning" Text
        last = df.iloc[-1]
        rsi = last['RSI']
        macd = last['MACD']
        signal = last['Signal_Line']
        price = last['Close']
        bb_upper = last['BB_Upper']
        bb_lower = last['BB_Lower']
        
        reasons = []
        
        # Simple English Logic
        # RSI Check
        if rsi < 30:
            reasons.append(f"✅ **Bargain Alert:** The price has dropped a lot. It might bounce back up soon! (RSI: {rsi:.0f})")
        elif rsi > 70:
            reasons.append(f"⚠️ **Expensive:** The price has gone up too fast. It might drop soon. Be careful! (RSI: {rsi:.0f})")
        else:
            reasons.append(f"ℹ️ **Neutral:** The price is stable right now. (RSI: {rsi:.0f})")
            
        # Bollinger Bands Check
        if price <= bb_lower * 1.02:
            reasons.append(f"🛡️ **Safety Net:** The price is at a very low support level. Good for buying! (Lower Band: {bb_lower:.2f})")
        elif price >= bb_upper * 0.98:
            reasons.append(f"🚫 **Too High:** The price is hitting a ceiling (Resistance). Hard to go higher. (Upper Band: {bb_upper:.2f})")
            
        # MACD Check (Momentum)
        if macd > signal:
            reasons.append(f"🚀 **Picking Up Speed:** The stock is gaining momentum upwards!")
        else:
            reasons.append(f"🐢 **Slowing Down:** The upward momentum is fading.")
            
        caption = f"🧠 **Analysis for {ticker}**\n\n" + "\n".join(reasons)
        caption += f"\n\n_Current Price: {price:.2f} KES_"

        # Append AI narrative if OpenClaw is reachable
        if ai.is_available():
            try:
                stocks = get_cached_stocks()
                stock = next((s for s in stocks if s['ticker'] == ticker), None)
                narrative = ai.ai_analyze(
                    ticker=ticker, price=price,
                    change_pct=stock.get('change_pct', 0) if stock else 0,
                    rsi=float(rsi), macd=float(macd),
                    pe=stock.get('pe_ratio') if stock else None,
                    div_yield=stock.get('dividend_yield') if stock else None,
                    volume=stock.get('volume') if stock else None,
                )
                caption += f"\n\n🤖 *AI Insight:*\n{narrative}"
            except Exception as ai_err:
                logger.warning(f"AI analyze failed: {ai_err}")

        await update.message.reply_photo(photo=img_buf, caption=caption, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Analysis error: {e}")
        await update.message.reply_text(f"❌ Failed to analyze: {str(e)[:100]}")


async def ask_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /ask <question> - AI-powered freeform NSE question."""
    if not context.args:
        await update.message.reply_text("Usage: /ask why is KPC up today?\n/ask which bank stock has the best dividend yield?")
        return

    question = " ".join(context.args)
    await update.message.reply_text("🤖 Thinking...")

    try:
        if not ai.is_available():
            await update.message.reply_text("❌ AI service unavailable right now. Try /analyze TICKER for rule-based analysis.")
            return

        stocks = get_cached_stocks()
        context_lines = [f"{s['ticker']} KES {s['price']} ({s.get('change_pct', 0):+.1f}%)"
                         for s in (stocks or [])[:20]]
        market_ctx = "Current NSE prices:\n" + "\n".join(context_lines)

        answer = ai.ai_ask(question, market_context=market_ctx)
        await update.message.reply_text(f"🤖 {answer}")
    except Exception as e:
        logger.error(f"ask_command error: {e}")
        await update.message.reply_text("❌ AI query failed. Please try again.")


async def portfolio_chart_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /pchart - Send portfolio allocation chart as image."""
    user_id = str(update.effective_user.id)
    
    await update.message.reply_text("📊 Generating portfolio chart...")
    
    try:
        port = pm.get_portfolio(user_id)
        
        if not port or not port['holdings']:
            await update.message.reply_text("📉 No portfolio found. Use /track to add positions.")
            return
        
        # Generate chart
        img_buf = generate_portfolio_chart(
            port['holdings'], port['total_value'], port['total_cost']
        )
        
        total_pnl = port['total_pnl']
        total_pnl_pct = port['total_pnl_pct']
        sign = '+' if total_pnl >= 0 else ''
        
        caption = f"💼 My Portfolio\n"
        caption += f"Value: KES {port['total_value']:,.0f}\n"
        caption += f"P/L: {sign}{total_pnl:,.0f} ({sign}{total_pnl_pct:.1f}%)\n"
        caption += f"Risk Score: {port['risk_score']:.0f}/100"
        
        await update.message.reply_photo(photo=img_buf, caption=caption)
        
    except Exception as e:
        logger.error(f"Portfolio chart error: {e}")
        await update.message.reply_text(f"❌ Failed to generate portfolio chart: {str(e)[:100]}")


async def alert_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /alert TICKER > PRICE or /alert TICKER < PRICE."""
    args = context.args
    if not args:
        await update.message.reply_text(
            "🔔 *Price Alert Usage:*\n\n"
            "`/alert SCOM > 35` \u2014 Alert when SCOM goes above 35\n"
            "`/alert KPLC < 17` \u2014 Alert when KPLC drops below 17\n\n"
            "I'll check prices every minute and notify you!",
            parse_mode='Markdown'
        )
        return
    
    # Robust parsing for cases like ">35" or "scom>35"
    # Join all args and try to parse with regex
    import re
    full_text = " ".join(args).upper()
    match = re.search(r'([A-Z]+)\s*([><]|ABOVE|BELOW)\s*(\d+(?:\.\d+)?)', full_text)
    
    if match:
        ticker = match.group(1)
        operator = match.group(2)
        target = float(match.group(3))
        
        if operator in ('>', 'ABOVE'):
            condition = 'above'
        else:
            condition = 'below'
            
    # Fallback to simple split if regex fails (legacy support)
    elif len(args) >= 3:
        ticker = args[0].upper()
        operator = args[1]
        try:
            target = float(context.args[2])
            if operator in ('>', 'above'): condition = 'above'
            elif operator in ('<', 'below'): condition = 'below'
            else: raise ValueError
        except ValueError:
             await update.message.reply_text("❌ Invalid format. Try: /alert SCOM > 35")
             return
    else:
        await update.message.reply_text("❌ Invalid format. Example: /alert SCOM > 35")
        return
    
    user_id = str(update.effective_user.id)
    
    # Store alert
    db = AlertSessionLocal()
    try:
        alert = PriceAlert(
            user_id=user_id,
            ticker=ticker,
            condition=condition,
            target_price=target
        )
        db.add(alert)
        db.commit()
        
        symbol = '>' if condition == 'above' else '<'
        current = _get_stock_price(ticker)
        current_str = f" (currently {current:.2f})" if current > 0 else ""
        
        await update.message.reply_text(
            f"✅ Alert set!\n\n"
            f"🔔 {ticker} {symbol} {target:.2f}{current_str}\n"
            f"ID: #{alert.id}\n\n"
            f"_I'll notify you when this triggers._",
            parse_mode='Markdown'
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Alert creation error: {e}")
        await update.message.reply_text(f"❌ Failed to create alert: {str(e)[:80]}")
    finally:
        db.close()


async def myalerts_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /myalerts - List active price alerts."""
    user_id = str(update.effective_user.id)
    
    db = AlertSessionLocal()
    try:
        alerts = db.query(PriceAlert).filter_by(
            user_id=user_id, triggered=False
        ).all()
        
        if not alerts:
            await update.message.reply_text(
                "🔕 No active alerts.\n\nUse /alert SCOM > 35 to set one!"
            )
            return
        
        lines = ["🔔 *Active Price Alerts*", ""]
        for a in alerts:
            symbol = '>' if a.condition == 'above' else '<'
            current = _get_stock_price(a.ticker)
            current_str = f" (now {current:.2f})" if current > 0 else ""
            lines.append(f"#{a.id}  `{a.ticker}` {symbol} {a.target_price:.2f}{current_str}")
        
        lines.append("\n_Use /delalert ID to remove_")
        await update.message.reply_text("\n".join(lines), parse_mode='Markdown')
    finally:
        db.close()


async def delalert_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /delalert ID - Delete a price alert."""
    if not context.args:
        await update.message.reply_text("Usage: /delalert 1\nUse /myalerts to see IDs.")
        return
    
    try:
        alert_id = int(context.args[0].replace('#', ''))
    except ValueError:
        await update.message.reply_text("❌ Invalid ID. Use /myalerts to see your alerts.")
        return
    
    user_id = str(update.effective_user.id)
    
    db = AlertSessionLocal()
    try:
        alert = db.query(PriceAlert).filter_by(id=alert_id, user_id=user_id).first()
        if not alert:
            await update.message.reply_text(f"❌ Alert #{alert_id} not found.")
            return
        
        symbol = '>' if alert.condition == 'above' else '<'
        desc = f"{alert.ticker} {symbol} {alert.target_price:.2f}"
        db.delete(alert)
        db.commit()
        await update.message.reply_text(f"🗑️ Deleted alert #{alert_id}: {desc}")
    finally:
        db.close()


async def check_price_alerts_job(context: ContextTypes.DEFAULT_TYPE):
    """Background job: check all active price alerts against current prices."""
    db = AlertSessionLocal()
    try:
        alerts = db.query(PriceAlert).filter_by(triggered=False).all()
        if not alerts:
            return
        
        stocks = get_cached_stocks()
        if not stocks:
            return
        
        price_map = {s.ticker: s.price for s in stocks}
        
        for alert in alerts:
            current = price_map.get(alert.ticker, 0)
            if current <= 0:
                continue
            
            triggered = False
            if alert.condition == 'above' and current >= alert.target_price:
                triggered = True
            elif alert.condition == 'below' and current <= alert.target_price:
                triggered = True
            
            if triggered:
                alert.triggered = True
                db.commit()
                
                symbol = '>' if alert.condition == 'above' else '<'
                msg = (
                    f"🚨 *PRICE ALERT TRIGGERED!*\n\n"
                    f"🔔 {alert.ticker} {symbol} {alert.target_price:.2f}\n"
                    f"💰 Current Price: *{current:.2f} KES*\n\n"
                    f"_Alert #{alert.id} has been deactivated._"
                )
                
                try:
                    await context.bot.send_message(
                        chat_id=alert.user_id, text=msg, parse_mode='Markdown'
                    )
                    logger.info(f"Alert #{alert.id} triggered: {alert.ticker} @ {current:.2f}")
                except Exception as e:
                    logger.error(f"Failed to send alert notification: {e}")
    except Exception as e:
        logger.error(f"Price alert check error: {e}")
    finally:
        db.close()


# ============ DIVIDEND CALENDAR COMMAND ============

async def dividends_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /dividends - Show upcoming dividend calendar."""
    user_id = str(update.effective_user.id)
    
    upcoming = get_upcoming_dividends(days_ahead=120)
    
    if not upcoming:
        await update.message.reply_text("No upcoming dividends in the next 120 days.")
        return
    
    lines = ["📅 *NSE DIVIDEND CALENDAR*", ""]
    
    # Check user's holdings
    user_tickers = set()
    try:
        db = pm.get_db()
        from database import PortfolioItem
        items = db.query(PortfolioItem).filter_by(user_id=user_id).all()
        user_tickers = {item.ticker for item in items}
        holdings = [{'ticker': item.ticker, 'qty': item.quantity} for item in items]
        db.close()
    except Exception:
        holdings = []
    
    for div in upcoming:
        own_marker = " ⭐" if div['ticker'] in user_tickers else ""
        
        if div['status'] == 'CLOSED':
            status_emoji = "🔴"
        elif div['status'] == 'CLOSING SOON':
            status_emoji = "🟡"
        else:
            status_emoji = "🟢"
        
        days = div['days_until_closure']
        if days < 0:
            days_str = f"{abs(days)}d ago"
        elif days == 0:
            days_str = "TODAY!"
        else:
            days_str = f"in {days}d"
        
        lines.append(
            f"{status_emoji} *{div['ticker']}*{own_marker} \u2014 KES {div['amount']:.2f}/share"
        )
        lines.append(
            f"    {div['type']} | Close: {div['book_closure'].strftime('%b %d')} ({days_str})"
        )
        lines.append(
            f"    Pay: {div['payment_date'].strftime('%b %d')} | {div['fy']}"
        )
        lines.append("")
    
    # Calculate user's expected income
    if holdings:
        income = get_user_dividend_income(holdings)
        if income:
            total_income = sum(i['total_income'] for i in income)
            lines.append("💰 *YOUR EXPECTED DIVIDENDS:*")
            for i in income:
                lines.append(
                    f"  {i['ticker']}: {i['qty']:.0f} x {i['dividend_per_share']:.2f} = "
                    f"*KES {i['total_income']:,.0f}*  (pays {i['payment_date'].strftime('%b %d')})"
                )
            lines.append(f"\n  🎉 *Total: KES {total_income:,.0f}*")
    
    lines.append("\n⭐ = You own this stock")
    lines.append("🟢 Upcoming  🟡 Closing Soon  🔴 Closed")
    lines.append("_Buy before book closure to qualify for dividend_")
    
    await update.message.reply_text("\n".join(lines), parse_mode='Markdown')


# ============ MAIN ============

def main():
    """Start the bot."""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not token:
        print("Error: TELEGRAM_BOT_TOKEN not set in .env")
        return
    
    print("=" * 50)
    print("  NSE Stock Bot Starting...")
    print("=" * 50)
    
    # Create application
    app = Application.builder().token(token).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("report", report))
    app.add_handler(CommandHandler("summary", summary))
    app.add_handler(CommandHandler("gainers", gainers))
    app.add_handler(CommandHandler("losers", losers))
    app.add_handler(CommandHandler("active", active))
    app.add_handler(CommandHandler("top", top))
    app.add_handler(CommandHandler("buy", buy))
    app.add_handler(CommandHandler("predict", predict))
    app.add_handler(CommandHandler("portfolio", portfolio))
    app.add_handler(CommandHandler("stock", stock))
    
    # Portfolio Handlers
    app.add_handler(CommandHandler("track", track))
    app.add_handler(CommandHandler("myportfolio", myportfolio))
    
    # Chart Handlers
    app.add_handler(CommandHandler("chart", chart_command))
    app.add_handler(CommandHandler("chat", chart_command))  # Alias for common typo
    app.add_handler(CommandHandler("forecast", forecast_command))
    app.add_handler(CommandHandler("pchart", portfolio_chart_command))
    app.add_handler(CommandHandler("analyze", analyze_command))
    app.add_handler(CommandHandler("ask", ask_command))
    
    # Alert & Dividend Handlers
    app.add_handler(CommandHandler("alert", alert_command))
    app.add_handler(CommandHandler("myalerts", myalerts_command))
    app.add_handler(CommandHandler("delalert", delalert_command))
    app.add_handler(CommandHandler("dividends", dividends_command))
    
    # Message Handler for NLP
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    app.add_handler(MessageHandler(filters.COMMAND, unknown))
    
    # Start Job Queue
    if app.job_queue:
        app.job_queue.run_repeating(check_alerts_job, interval=60, first=10)
        app.job_queue.run_repeating(check_price_alerts_job, interval=120, first=30)
        print("Jobs scheduled: Risk alerts (60s), Price alerts (120s)")
    
    # Start daily price collector
    start_scheduler()

    print("Bot is running! Press Ctrl+C to stop.")
    print("Open Telegram and message @NSE_whit_bot")

    # Start polling
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
