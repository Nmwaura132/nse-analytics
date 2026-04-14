"""
Correctness verification for NSE Pro production changes.
Run from nse_pro/ directory.
"""
import sys, types, math, importlib.util
import numpy as np
import pandas as pd

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"
all_passed = True

def check(name, condition, msg=""):
    global all_passed
    if condition:
        print(f"  {PASS}  {name}")
    else:
        print(f"  {FAIL}  {name}  — {msg}")
        all_passed = False

# ─────────────────────────────────────────────────────────────────────────────
print("\n══ Test 1: Sharpe Ratio & Kelly Criterion ══\n")

src = open("advanced_algorithms.py", encoding="utf-8").read()
ns = {"math": math, "__builtins__": __builtins__}
exec(compile(src, "advanced_algorithms.py", "exec"), ns)

Algo  = ns["AdvancedPortfolioAlgorithms"]
Stock = ns["EnhancedStock"]

def make_stock(price, change, momentum=60):
    s = Stock.__new__(Stock)
    s.price = price; s.change = change; s.momentum_score = momentum
    s.volume = 1_000_000; s.change_pct = change / price * 100
    s.composite_score = s.sharpe_ratio = s.kelly_fraction = s.risk_score = 0
    s.is_gainer = change > 0; s.is_loser = change < 0
    s.ticker = "TEST"; s.name = "Test"
    return s

algo = Algo.__new__(Algo)
algo.stocks = []
algo._compute_market_stats()

# Gaining stock: +2% → Sharpe and Kelly must be > 0
g = make_stock(100, 2.0)
sharpe_g = algo.calculate_sharpe_ratio(g)
kelly_g  = algo.calculate_kelly_fraction(g)
check("Sharpe > 0 for gaining stock", sharpe_g > 0, f"got {sharpe_g:.4f}")
check("Kelly > 0 for gaining stock",  kelly_g  > 0, f"got {kelly_g:.4f}")

# Losing stock: -5% → Kelly must be 0 or marginally positive
l = make_stock(100, -5.0, momentum=20)
sharpe_l = algo.calculate_sharpe_ratio(l)
kelly_l  = algo.calculate_kelly_fraction(l)
check("Sharpe < 0 for losing stock",  sharpe_l < 0, f"got {sharpe_l:.4f}")
check("Kelly >= 0 (no short selling)", kelly_l >= 0, f"got {kelly_l:.4f}")

# DAILY_PERSISTENCE_FACTOR is 0.15 (not 0.05)
check(
    "DAILY_PERSISTENCE_FACTOR = 0.15",
    Algo.DAILY_PERSISTENCE_FACTOR == 0.15,
    f"got {Algo.DAILY_PERSISTENCE_FACTOR}",
)

# ─────────────────────────────────────────────────────────────────────────────
print("\n══ Test 2: MLPredictor — out-of-sample MSE & model cache ══\n")

# Stub missing modules so ml_predictor.py can be loaded standalone
fake_hg = types.ModuleType("history_generator")
fake_hg.generate_stock_history = lambda *a, **kw: pd.DataFrame()
sys.modules.setdefault("history_generator", fake_hg)

fake_rf = types.ModuleType("real_data_fetcher")
class FakeFetcher:
    def get_history(self, *a, **kw): return None
fake_rf.YFinanceNSEFetcher = FakeFetcher
sys.modules["real_data_fetcher"] = fake_rf

spec = importlib.util.spec_from_file_location("ml_predictor", "ml_predictor.py")
ml_mod = importlib.util.module_from_spec(spec)
sys.modules["ml_predictor"] = ml_mod
spec.loader.exec_module(ml_mod)
MLPredictor = ml_mod.MLPredictor

np.random.seed(42)
n = 252
prices = 100 + np.cumsum(np.random.randn(n) * 0.5)
df = pd.DataFrame({
    "Date":   pd.date_range("2024-01-01", periods=n),
    "Open":   prices * 0.99,
    "High":   prices * 1.01,
    "Low":    prices * 0.98,
    "Close":  prices,
    "Volume": np.random.randint(100_000, 1_000_000, n).astype(float),
})
df.attrs["is_real_data"] = False

pred = MLPredictor()
result = pred.predict_next_price(df, ticker="SYNTHETIC")

check("No error in result",              "error" not in result,                          str(result))
check("mse_type = out_of_sample",        result.get("mse_type") == "out_of_sample",      result.get("mse_type"))
check("is_real_data = False (simulated)", result.get("is_real_data") is False,            str(result.get("is_real_data")))
check("MSE is non-negative float",        isinstance(result.get("mse"), float) and result["mse"] >= 0, str(result.get("mse")))
check("predicted_price is float",         isinstance(result.get("predicted_price"), float), type(result.get("predicted_price")))

# Model should now be cached
check("Model cached after first call",   "SYNTHETIC" in pred.models)
result2 = pred.predict_next_price(df, ticker="SYNTHETIC")
check("Second call uses cached model",   result["mse"] == result2["mse"], "MSE differ (model retrained)")

print(f"\nCache TTL: {MLPredictor.MODEL_TTL_SECONDS}s (24h)")
check("MODEL_TTL_SECONDS = 86400",       MLPredictor.MODEL_TTL_SECONDS == 86_400)

# ─────────────────────────────────────────────────────────────────────────────
print("\n══ Test 3: comprehensive_analyzer — no duplicate method ══\n")

src = open("comprehensive_analyzer.py", encoding="utf-8").read()
import ast
tree = ast.parse(src)

for classdef in ast.walk(tree):
    if isinstance(classdef, ast.ClassDef) and classdef.name == "ComprehensiveAnalyzer":
        method_names = [n.name for n in classdef.body if isinstance(n, ast.FunctionDef)]
        dupes = [m for m in set(method_names) if method_names.count(m) > 1]
        check("No duplicate methods in ComprehensiveAnalyzer", dupes == [], f"Duplicates: {dupes}")

# Verify calculate_momentum_score signature has min_change, max_change params
for classdef in ast.walk(tree):
    if isinstance(classdef, ast.ClassDef) and classdef.name == "ComprehensiveAnalyzer":
        for node in classdef.body:
            if isinstance(node, ast.FunctionDef) and node.name == "calculate_momentum_score":
                params = [a.arg for a in node.args.args]
                check(
                    "calculate_momentum_score takes min_change, max_change",
                    "min_change" in params and "max_change" in params,
                    f"params: {params}"
                )

# ─────────────────────────────────────────────────────────────────────────────
print("\n══ Test 4: data_fetcher — no dead return statements ══\n")

src = open("data_fetcher.py", encoding="utf-8").read()
check("No duplicate 'return df\\n\\n            return df'", "return df\n\n            return df" not in src)
check("No duplicate 'return result\\n\\n            return result'", "return result\n\n            return result" not in src)

# ─────────────────────────────────────────────────────────────────────────────
print("\n══ Test 5: nse_bot.py — no debug print, single load_dotenv ══\n")

src5 = open("nse_bot.py", encoding="utf-8").read()
check('No debug print', 'print("DEBUG:' not in src5)
check('load_dotenv called once', src5.count('load_dotenv()') == 1)
check('Lock lazily init (not at module level)', '_cache_lock: asyncio.Lock | None = None' in src5)
check('get_running_loop used (not get_event_loop)', 'get_running_loop()' in src5 and 'get_event_loop()' not in src5)
check('/ask handler registered', 'CommandHandler("ask"' in src5)
check('RotatingFileHandler present', 'RotatingFileHandler' in src5)
check('SIGTERM handler present', 'signal.SIGTERM' in src5)

# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*55)
if all_passed:
    print("  ALL CHECKS PASSED ✓")
else:
    print("  SOME CHECKS FAILED — see above")
    sys.exit(1)
