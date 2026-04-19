import asyncio
import os
from dotenv import load_dotenv
import pandas as pd
from data_fetcher import NSEDataFetcher
from analyzer import MarketAnalyzer
from notifier import TelegramNotifier
import logging
import time

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def run_analysis_cycle():
    load_dotenv()
    
    fetcher = NSEDataFetcher()
    analyzer = MarketAnalyzer()
    notifier = TelegramNotifier()
    
    logger.info("Starting NSE Market Analysis...")
    await notifier.send_message("🔍 *Starting NSE Market Analysis...*")
    
    # 1. Fetch Companies
    companies = fetcher.get_nse_companies()
    logger.info(f"Found {len(companies)} companies.")
    
    if not companies:
        logger.error("No companies found. Aborting.")
        await notifier.send_message("⚠️ Error: Could not fetch company list.")
        return

    # 2. Fetch History and Analyze (limit to top 10 for testing or specific list if preferred)
    # For a full run, we would iterate all. For now, let's try a subset to be fast.
    # checking commonly traded stocks
    priority_tickers = ['SCOM', 'EQTY', 'KCB', 'EABL', 'COOP', 'ABSA', 'NCBA', 'BAT', 'KNRE', 'CTUM']
    
    analyzed_count = 0
    results = {'opportunities': [], 'alerts': []}
    
    # Filter companies to prioritize or take first N
    # We will prioritize the list above, then add others? 
    # Or just run for the priority list for the MVP.
    target_tickers = [c['ticker'] for c in companies if c['ticker'] in priority_tickers]
    
    # Fallback if scraping didn't find them (maybe naming mismatch?)
    if not target_tickers:
        target_tickers = priority_tickers 

    logger.info(f"Analyzing {len(target_tickers)} priority stocks...")
    
    for ticker in target_tickers:
        logger.info(f"Fetching {ticker}...")
        df = fetcher.get_stock_history(ticker)
        
        if not df.empty:
            analysis = analyzer.analyze_stock(ticker, df)
            if analysis:
                analyzed_count += 1
                if analysis['buy_signal']:
                    results['opportunities'].append(analysis)
                if analysis['alert_signal']:
                    results['alerts'].append(analysis)
        
        # Be polite to the server
        time.sleep(1) 

    # 3. Report Results
    report = f"📊 *NSE Market Report*\nAnalyzed {analyzed_count} stocks.\n\n"
    
    if results['opportunities']:
        report += "🚀 *Investment Opportunities (Uptrend + Momentum)*:\n"
        for opp in results['opportunities']:
            price_fmt = f"{opp['price']:.2f}"
            change_fmt = f"{opp['change_pct']:+.2f}%"
            report += f"- *{opp['ticker']}*: KES {price_fmt} ({change_fmt})\n"
    else:
        report += "No strong buy signals detected.\n"
        
    if results['alerts']:
        report += "\n⚠️ *Market Alerts (Volatility/Large Moves)*:\n"
        for alert in results['alerts']:
             report += f"- *{alert['ticker']}*: {alert['alert_reason']}\n"

    logger.info("Sending report...")
    await notifier.send_message(report)
    logger.info("Cycle complete.")

if __name__ == "__main__":
    asyncio.run(run_analysis_cycle())
