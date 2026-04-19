from comprehensive_analyzer import ComprehensiveAnalyzer

def check_picks():
    print("Fetching Real-Time Data (ABSA/KPLC)...")
    analyzer = ComprehensiveAnalyzer()
    stocks = analyzer.analyze_all_stocks()
    
    targets = ['ABSA', 'KPLC', 'SCOM']
    for t in targets:
        s = next((x for x in stocks if x.ticker == t), None)
        if s:
            print(f"\n--- {t} ---")
            print(f"Current Price: {s.price}")
            print(f"Change: {s.change} ({s.change_pct}%)")
            print(f"Volume: {s.volume}")
            
if __name__ == "__main__":
    check_picks()
