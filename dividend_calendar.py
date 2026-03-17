"""
NSE Dividend Calendar
Tracks upcoming dividend announcements, book closures, and payment dates.
Data sourced from NSE corporate actions and news.
"""
from datetime import datetime, date

# Dividend data — update periodically from NSE/Business Daily
# Format: {ticker: [{type, amount, book_closure, payment_date, fy}]}
DIVIDEND_CALENDAR = [
    {
        'ticker': 'SCOM',
        'name': 'Safaricom PLC',
        'type': 'Interim',
        'amount': 0.85,
        'book_closure': date(2026, 2, 25),
        'payment_date': date(2026, 3, 31),
        'fy': 'FY Mar 2026',
    },
    {
        'ticker': 'KPLC',
        'name': 'Kenya Power & Lighting',
        'type': 'Interim',
        'amount': 0.30,
        'book_closure': date(2026, 2, 23),
        'payment_date': date(2026, 3, 27),
        'fy': 'HY Dec 2025',
    },
    {
        'ticker': 'EABL',
        'name': 'East African Breweries',
        'type': 'Interim',
        'amount': 4.00,
        'book_closure': date(2026, 2, 20),
        'payment_date': date(2026, 4, 30),
        'fy': 'HY Dec 2025',
    },
    {
        'ticker': 'SCBK',
        'name': 'Standard Chartered Kenya',
        'type': 'Final',
        'amount': 28.00,
        'book_closure': date(2026, 4, 15),
        'payment_date': date(2026, 5, 30),
        'fy': 'FY Dec 2025',
    },
    {
        'ticker': 'BAT',
        'name': 'BAT Kenya',
        'type': 'Final',
        'amount': 55.00,
        'book_closure': date(2026, 4, 25),
        'payment_date': date(2026, 6, 15),
        'fy': 'FY Dec 2025',
    },
    {
        'ticker': 'EQTY',
        'name': 'Equity Group',
        'type': 'Final',
        'amount': 4.00,
        'book_closure': date(2026, 4, 10),
        'payment_date': date(2026, 5, 20),
        'fy': 'FY Dec 2025',
    },
    {
        'ticker': 'KCB',
        'name': 'KCB Group',
        'type': 'Final',
        'amount': 2.50,
        'book_closure': date(2026, 4, 18),
        'payment_date': date(2026, 5, 28),
        'fy': 'FY Dec 2025',
    },
    {
        'ticker': 'COOP',
        'name': 'Co-operative Bank',
        'type': 'Final',
        'amount': 1.50,
        'book_closure': date(2026, 4, 20),
        'payment_date': date(2026, 6, 5),
        'fy': 'FY Dec 2025',
    },
    {
        'ticker': 'ABSA',
        'name': 'Absa Bank Kenya',
        'type': 'Final',
        'amount': 1.35,
        'book_closure': date(2026, 4, 22),
        'payment_date': date(2026, 5, 30),
        'fy': 'FY Dec 2025',
    },
    {
        'ticker': 'SBIC',
        'name': 'Stanbic Holdings',
        'type': 'Final',
        'amount': 14.20,
        'book_closure': date(2026, 4, 12),
        'payment_date': date(2026, 5, 15),
        'fy': 'FY Dec 2025',
    },
]


def get_upcoming_dividends(days_ahead: int = 90) -> list:
    """Get dividends with book closure within the next N days."""
    today = date.today()
    upcoming = []
    for div in DIVIDEND_CALENDAR:
        days_until = (div['book_closure'] - today).days
        if days_until >= -7 and days_until <= days_ahead:  # Include recently passed (7 days)
            div_copy = dict(div)
            div_copy['days_until_closure'] = days_until
            div_copy['status'] = 'CLOSED' if days_until < 0 else 'CLOSING SOON' if days_until <= 7 else 'UPCOMING'
            upcoming.append(div_copy)
    
    # Sort by book closure date
    upcoming.sort(key=lambda x: x['book_closure'])
    return upcoming


def get_user_dividend_income(holdings: list) -> list:
    """
    Calculate expected dividend income for user's holdings.
    
    Args:
        holdings: list of dicts with 'ticker' and 'qty' keys
    
    Returns:
        list of dicts with ticker, qty, dividend_amount, total_income
    """
    today = date.today()
    income = []
    
    holding_map = {h['ticker']: h['qty'] for h in holdings}
    
    for div in DIVIDEND_CALENDAR:
        if div['ticker'] in holding_map:
            days_until = (div['book_closure'] - today).days
            if days_until >= -1:  # Not yet closed or just closed
                qty = holding_map[div['ticker']]
                total = qty * div['amount']
                income.append({
                    'ticker': div['ticker'],
                    'qty': qty,
                    'dividend_per_share': div['amount'],
                    'total_income': total,
                    'payment_date': div['payment_date'],
                    'book_closure': div['book_closure'],
                })
    
    return income
