import requests
from comprehensive_analyzer import ComprehensiveAnalyzer
import datetime

def check_system():
    print("--- SYSTEM HEALTH CHECK ---")
    print(f"Time: {datetime.datetime.now()}")
    
    # 1. Check Dashboard Server
    try:
        r = requests.get('http://127.0.0.1:5001/api/summary', timeout=2)
        if r.status_code == 200:
            data = r.json()
            print("[PASS] Dashboard Server is UP")
            print(f"       Total Stocks: {data.get('total')}")
            last_up = data.get('last_update')
            if last_up:
                dt = datetime.datetime.fromtimestamp(last_up)
                print(f"       Last Data Update: {dt}")
            else:
                print("       [WARN] No last_update timestamp.")
        else:
            print(f"[FAIL] Dashboard Server returned {r.status_code}")
    except Exception as e:
        print(f"[FAIL] Dashboard Server unreachable: {e}")

    # 2. Check Data Feed
    try:
        analyzer = ComprehensiveAnalyzer()
        # Peek at one stock without full fetch if possible? 
        # analyze_all_stocks uses cache if available.
        # But we want to know if cache is stale.
        # dashboard_server handles cache. analyzer might fetch fresh.
        print("Checking Analyzer...")
        stocks = analyzer.analyze_all_stocks()
        if stocks:
            scom = next((s for s in stocks if s.ticker == 'SCOM'), None)
            if scom:
                print(f"[PASS] Data Feed Active. SCOM Price: {scom.price}")
            else:
                print("[WARN] SCOM not found?")
        else:
            print("[FAIL] No stocks returned.")
    except Exception as e:
        print(f"[FAIL] Analyzer Error: {e}")

if __name__ == "__main__":
    check_system()
