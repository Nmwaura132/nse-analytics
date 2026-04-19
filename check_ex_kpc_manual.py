
# Manual Calculation for Ex-KPC Portfolio
# Holdings verified from DB:
# BRIT: 20 @ 10.37
# SCOM: 19 @ 32.63
# KPLC: 60 @ 17.79
# ABSA: 36 @ 29.45

holdings = [
    {'ticker': 'BRIT', 'qty': 20, 'cost': 10.37, 'price': 11.65},
    {'ticker': 'SCOM', 'qty': 19, 'cost': 32.63, 'price': 34.00},
    {'ticker': 'KPLC', 'qty': 60, 'cost': 17.79, 'price': 18.35},
    {'ticker': 'ABSA', 'qty': 36, 'cost': 29.45, 'price': 30.00}
]

total_cost = 0
total_value = 0

print("--- Active Trading Portfolio (Ex-KPC) [Manual Estimate] ---")
print(f"{'Ticker':<6} {'Qty':<5} {'Cost':<8} {'Price':<8} {'Value':<8} {'PnL'}")
print("-" * 60)

for h in holdings:
    cost_val = h['qty'] * h['cost']
    curr_val = h['qty'] * h['price']
    pnl = curr_val - cost_val
    pnl_pct = (pnl / cost_val) * 100
    
    total_cost += cost_val
    total_value += curr_val
    
    symbol = "🟢" if pnl >= 0 else "🔴"
    print(f"{h['ticker']:<6} {h['qty']:<5} {h['cost']:<8.2f} {h['price']:<8.2f} {curr_val:<8.0f} {symbol} {pnl_pct:.2f}%")

print("-" * 60)
total_pnl = total_value - total_cost
total_pnl_pct = (total_pnl / total_cost) * 100
market_symbol = "🟢" if total_pnl >= 0 else "🔴"

print(f"Total Invested: KES {total_cost:,.2f}")
print(f"Current Value:  KES {total_value:,.2f}")
print(f"Total PnL:      {market_symbol} KES {total_pnl:,.2f} ({total_pnl_pct:.2f}%)")
