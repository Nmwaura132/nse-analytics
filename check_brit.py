from comprehensive_analyzer import ComprehensiveAnalyzer

def check_brit():
    print("Fetching BRIT data...")
    analyzer = ComprehensiveAnalyzer()
    stocks = analyzer.analyze_all_stocks()
    
    brit = next((s for s in stocks if s.ticker == 'BRIT'), None)
    
    if brit:
        print(f"\n--- BRIT ANALYSIS ---")
        print(f"Current Price: {brit.price}")
        print(f"Change: {brit.change} ({brit.change_pct}%)")
        print(f"Volume: {brit.volume}")
        print(f"Score: {brit.composite_score}")
        
        if brit.volume < 1000:
            print("WARNING: Very Low Liquidity (Hard to buy/sell)")
        elif brit.volume > 100000:
            print("STATUS: High Liquidity")
            
        if brit.change > 0:
            print("TREND: Price is Rising (Sellers demanding more)")
        elif brit.change < 0:
            print("TREND: Price is Falling")
        else:
            print("TREND: Flat")
    else:
        print("BRIT not found in data feed.")

if __name__ == "__main__":
    check_brit()
