"""
NSE Financials Module
Stores hardcoded fundamental data (EPS, DPS, Book Value) for top stocks
and calculates dynamic valuation metrics.
Data Source: Latest FY/HY Reports (2023-2024)
"""
from typing import Dict, Optional
import math

# Manual Data: Ticker -> {eps, dps, book_value_per_share}
# EPS: Earnings Per Share (Trailing 12M)
# DPS: Dividend Per Share (Trailing 12M)
# BVPS: Book Value Per Share (Latest Equity / Shares)
FUNDAMENTALS = {
    'SCOM': {'name': 'Safaricom', 'eps': 1.63, 'dps': 1.20, 'bvps': 3.48, 'sector': 'Telco'},
    'EQTY': {'name': 'Equity Group', 'eps': 11.12, 'dps': 4.00, 'bvps': 54.20, 'sector': 'Banking'},
    'KCB': {'name': 'KCB Group', 'eps': 12.30, 'dps': 0.00, 'bvps': 68.50, 'sector': 'Banking'}, # suspended div
    'EABL': {'name': 'EABL', 'eps': 8.90, 'dps': 6.00, 'bvps': 22.40, 'sector': 'Manufacturing'},
    'COOP': {'name': 'Co-operative Bank', 'eps': 4.30, 'dps': 1.50, 'bvps': 21.80, 'sector': 'Banking'},
    'ABSA': {'name': 'Absa Bank Kenya', 'eps': 3.10, 'dps': 1.35, 'bvps': 12.60, 'sector': 'Banking'},
    'NCBA': {'name': 'NCBA Group', 'eps': 13.50, 'dps': 4.75, 'bvps': 55.30, 'sector': 'Banking'},
    'SCBK': {'name': 'StanChart Kenya', 'eps': 38.40, 'dps': 29.00, 'bvps': 165.20, 'sector': 'Banking'},
    'BAT': {'name': 'BAT Kenya', 'eps': 53.00, 'dps': 50.00, 'bvps': 130.00, 'sector': 'Manufacturing'},
    'DTK': {'name': 'Diamond Trust Bank', 'eps': 23.00, 'dps': 6.00, 'bvps': 240.00, 'sector': 'Banking'},
    'I&M': {'name': 'I&M Holdings', 'eps': 7.60, 'dps': 2.55, 'bvps': 48.00, 'sector': 'Banking'},
    'KPLC': {'name': 'Kenya Power', 'eps': 1.53, 'dps': 0.00, 'bvps': 28.00, 'sector': 'Energy'},
    'KENGEN': {'name': 'KenGen', 'eps': 0.76, 'dps': 0.30, 'bvps': 34.00, 'sector': 'Energy'},
    'JUB': {'name': 'Jubilee Holdings', 'eps': 105.00, 'dps': 12.00, 'bvps': 580.00, 'sector': 'Insurance'},
    'BAMB': {'name': 'Bamburi Cement', 'eps': 1.80, 'dps': 0.75, 'bvps': 78.00, 'sector': 'Manufacturing'},
    'CICP': {'name': 'CIC Insurance', 'eps': 0.52, 'dps': 0.13, 'bvps': 3.10, 'sector': 'Insurance'},
    'BRIT': {'name': 'Britam', 'eps': 0.65, 'dps': 0.00, 'bvps': 7.80, 'sector': 'Insurance'},
    'NSE': {'name': 'Nairobi Securities Exchange', 'eps': 0.15, 'dps': 0.15, 'bvps': 7.90, 'sector': 'Financial'},
    'TOTL': {'name': 'TotalEnergies', 'eps': 4.20, 'dps': 1.31, 'bvps': 45.00, 'sector': 'Energy'},
    'CARB': {'name': 'Carbacid', 'eps': 2.80, 'dps': 1.70, 'bvps': 14.50, 'sector': 'Manufacturing'},
}

def get_fundamentals(ticker: str) -> Optional[Dict]:
    """Retrieve static fundamental data for a ticker."""
    return FUNDAMENTALS.get(ticker.upper())

def calculate_valuation_metrics(ticker: str, current_price: float) -> Dict:
    """
    Calculate dynamic valuation metrics based on live price.
    Returns:
        {
            'pe_ratio': float,
            'dividend_yield': float, # %
            'pb_ratio': float,
            'graham_number': float,
            'intrinsic_status': str, # Undervalued/Fair/Overvalued
            'sector': str
        }
    """
    data = FUNDAMENTALS.get(ticker.upper())
    if not data or not current_price or current_price <= 0:
        return {}
    
    eps = data['eps']
    dps = data['dps']
    bvps = data['bvps']
    
    # P/E Ratio
    pe = current_price / eps if eps > 0 else 0
    
    # Dividend Yield
    div_yield = (dps / current_price) * 100 if current_price > 0 else 0
    
    # P/B Ratio
    pb = current_price / bvps if bvps > 0 else 0
    
    # Graham Number = Sqrt(22.5 * EPS * BVPS)
    # Conservative valuation for defensive investors
    graham_number = 0
    if eps > 0 and bvps > 0:
        graham_number = math.sqrt(22.5 * eps * bvps)
        
    # Valuation Status
    status = "Fair Value"
    if graham_number > 0:
        if current_price < graham_number * 0.8:
            status = "Undervalued 🟢"
        elif current_price > graham_number * 1.2:
            status = "Overvalued 🔴"
            
    return {
        'pe_ratio': round(pe, 2),
        'dividend_yield': round(div_yield, 2),
        'pb_ratio': round(pb, 2),
        'graham_number': round(graham_number, 2),
        'intrinsic_status': status,
        'sector': data['sector'],
        'eps': eps,
        'dps': dps
    }

if __name__ == "__main__":
    # Test
    print(calculate_valuation_metrics("SCOM", 14.50))
    print(calculate_valuation_metrics("EQTY", 45.00))
