import time
import pandas as pd
import numpy as np
from datetime import datetime

# External logic imports from nse_pro root
try:
    from comprehensive_analyzer import ComprehensiveAnalyzer
    from advanced_algorithms import enhance_stocks
    import financials
    from ml_predictor import MLPredictor
    from ml_optimizer import MLOptimizer
    from backtester import Backtester
except ImportError:
    pass

class MarketService:
    """Service layer for handling market data, caching, and ML logic."""
    
    _market_cache = {
        'last_update': None,
        'stocks': [],
        'enhanced': [],
        'algo': None,
        'summary': {}
    }
    _cache_ttl = 120
    _predictor_instance = None
    _analyzer_instance = None

    @classmethod
    def get_analyzer(cls):
        if cls._analyzer_instance is None:
            cls._analyzer_instance = ComprehensiveAnalyzer()
        return cls._analyzer_instance

    @classmethod
    def get_predictor(cls):
        if cls._predictor_instance is None:
            cls._predictor_instance = MLPredictor()
        return cls._predictor_instance

    @classmethod
    def refresh_data(cls):
        print("Refreshing market data...")
        stocks = cls.get_analyzer().analyze_all_stocks()
        if not stocks:
            return
        
        enhanced, algo = enhance_stocks(stocks)
        gainers = [s for s in stocks if s.is_gainer]
        losers = [s for s in stocks if s.is_loser]
        
        cls._market_cache['stocks'] = stocks
        cls._market_cache['enhanced'] = enhanced
        cls._market_cache['algo'] = algo
        cls._market_cache['summary'] = {
            'total': len(stocks),
            'gainers_count': len(gainers),
            'losers_count': len(losers),
            'unchanged_count': len(stocks) - len(gainers) - len(losers),
            'buy_candidates_count': len([s for s in stocks if s.composite_score >= 50 and s.is_gainer])
        }
        cls._market_cache['last_update'] = time.time()

    @classmethod
    def get_data(cls):
        if (not cls._market_cache['stocks'] or 
            (time.time() - (cls._market_cache['last_update'] or 0)) > cls._cache_ttl):
            cls.refresh_data()
        return cls._market_cache

    @staticmethod
    def sanitize_float(obj):
        """Sanitize floats, NaNs, and Infinities for JSON serialization."""
        if isinstance(obj, float):
            if np.isnan(obj) or np.isinf(obj):
                return None
            return obj
        elif isinstance(obj, (dict, list)):
            return MarketService.sanitize_json(obj)
        return obj

    @staticmethod
    def sanitize_json(obj):
        if isinstance(obj, dict):
            return {k: MarketService.sanitize_float(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [MarketService.sanitize_float(v) for v in obj]
        elif isinstance(obj, pd.Series):
            return MarketService.sanitize_json(obj.to_dict())
        return MarketService.sanitize_float(obj)
