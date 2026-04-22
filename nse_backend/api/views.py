import time
from datetime import datetime, timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.utils import timezone
from django.shortcuts import get_object_or_404
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import financials
from ml_optimizer import MLOptimizer

from .models import Trade, UserProfile, Subscription
from .serializers import TradeSerializer, MarketSummarySerializer, NotificationSerializer
from .services import MarketService
from .mpesa import stk_push, TIER_PRICES
from .permissions import IsPro

# Notifications Queue (Simple in-memory queue)
notifications_queue = []
MAX_NOTIFICATIONS = 50

class StockListView(APIView):
    """List all stocks with basic valuation metrics."""
    def get(self, request):
        cache = MarketService.get_data()
        stocks_data = []
        for s in cache['stocks']:
            valuation = financials.calculate_valuation_metrics(s.ticker, s.price)
            stocks_data.append({
                'ticker': s.ticker,
                'name': s.name,
                'price': s.price,
                'change': s.change,
                'pe': valuation.get('pe_ratio'),
                'yield': valuation.get('dividend_yield'),
                'sector': valuation.get('sector')
            })
        stocks_data.sort(key=lambda x: x['ticker'])
        return Response(stocks_data)

class StockDetailView(APIView):
    """Retrieve detailed analysis for a specific stock."""
    def get(self, request, ticker):
        cache = MarketService.get_data()
        enhanced = cache.get('enhanced', [])
        algo = cache.get('algo')
        
        if not enhanced or not algo:
            return Response({'error': 'Data initializing'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
        stock_obj = next((s for s in enhanced if s.ticker.upper() == ticker.upper()), None)
        if not stock_obj:
            return Response({'error': 'Stock not found'}, status=status.HTTP_404_NOT_FOUND)
            
        emoji, signal, conf = algo.get_signal(stock_obj)
        price = stock_obj.price or 0.0
        change = stock_obj.change or 0.0
        
        data = {
            'ticker': stock_obj.ticker,
            'name': stock_obj.name,
            'price': price,
            'volume': stock_obj.volume,
            'change': change,
            'change_pct': stock_obj.change_pct or ((change / (price - change) * 100) if price and change else 0),
            'valuation': financials.calculate_valuation_metrics(stock_obj.ticker, price),
            'scores': {
                'momentum': stock_obj.momentum_score,
                'volume': stock_obj.volume_score,
                'composite': stock_obj.composite_score,
            },
            'advanced': {
                'sharpe': stock_obj.sharpe_ratio,
                'risk': stock_obj.risk_score,
                'kelly': stock_obj.kelly_fraction,
            },
            'signal': f"{emoji} {signal}",
            'confidence': conf
        }
        return Response(MarketService.sanitize_json(data))

class RefreshDataView(APIView):
    """Force refresh market data."""
    def post(self, request):
        MarketService.refresh_data()
        return Response({'status': 'ok', 'message': 'Market data refreshed'})

class PortfolioListView(APIView):
    """Get portfolio holdings and performance summary."""
    def get(self, request):
        user_id = request.query_params.get('user_id', '1')
        trades = Trade.objects.filter(user_id=user_id)
        
        market = MarketService.get_data()
        price_map = {s.ticker: s.price for s in market['stocks']}
        
        holdings = []
        total_val = 0
        total_cost = 0
        
        for t in trades:
            curr_price = price_map.get(t.ticker, t.avg_cost)
            val = t.qty * curr_price
            cost = t.qty * t.avg_cost
            pnl = val - cost
            
            # Use serializer for consistent output
            serializer = TradeSerializer(t)
            trade_data = serializer.data
            trade_data.update({
                'current_price': curr_price,
                'pnl': pnl,
                'pnl_pct': (pnl / cost * 100) if cost > 0 else 0
            })
            holdings.append(trade_data)
            
            total_val += val
            total_cost += cost
            
        return Response({
            'holdings': holdings,
            'summary': {
                'total_value': total_val,
                'total_pnl': total_val - total_cost,
                'pnl_pct': ((total_val - total_cost) / total_cost * 100) if total_cost > 0 else 0,
                'risk_score': 50.0  # Placeholder for complex risk engine
            },
            'is_offline': not bool(market['stocks'])
        })

class AddTradeView(APIView):
    """Add or update a trade in the portfolio."""
    def post(self, request):
        serializer = TradeSerializer(data=request.data)
        if serializer.is_valid():
            ticker = serializer.validated_data['ticker']
            user_id = serializer.validated_data.get('user_id', '1')
            qty = serializer.validated_data['qty']
            price = serializer.validated_data['avg_cost']
            
            trade, created = Trade.objects.get_or_create(user_id=user_id, ticker=ticker)
            if created:
                trade.qty = qty
                trade.avg_cost = price
            else:
                total_qty = trade.qty + qty
                trade.avg_cost = ((trade.avg_cost * trade.qty) + (price * qty)) / total_qty
                trade.qty = total_qty
            trade.save()
            return Response({'success': True, 'message': 'Trade recorded'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RemoveTradeView(APIView):
    """Remove a stock from the portfolio."""
    def post(self, request):
        ticker = request.data.get('ticker')
        user_id = request.data.get('user_id', '1')
        Trade.objects.filter(user_id=user_id, ticker=ticker).delete()
        return Response({'success': True, 'message': 'Ticker removed'})

class OptimizePortfolioView(APIView):
    """Suggest an optimal portfolio allocation using ML."""
    def post(self, request):
        budget = float(request.data.get('budget', 100000))
        tickers = request.data.get('tickers', [])
        
        if not tickers:
            top = sorted(MarketService.get_data().get('enhanced', []), 
                         key=lambda x: x.composite_score, reverse=True)[:5]
            tickers = [s.ticker for s in top]
            
        optimizer = MLOptimizer()
        results = optimizer.get_optimal_allocation(tickers, budget)
        return Response(MarketService.sanitize_json(results))

class NotificationView(APIView):
    """Fetch or push market notifications."""
    def get(self, request):
        return Response(notifications_queue[::-1])
        
    def post(self, request):
        serializer = NotificationSerializer(data=request.data)
        if serializer.is_valid():
            notif = {
                'id': int(time.time() * 1000),
                'timestamp': datetime.now().strftime("%H:%M:%S"),
                'message': serializer.validated_data['message'],
                'type': serializer.validated_data['type']
            }
            notifications_queue.append(notif)
            if len(notifications_queue) > MAX_NOTIFICATIONS:
                notifications_queue.pop(0)
            return Response({'status': 'success'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Data Science Endpoints
class BacktestView(APIView):
    def get(self, request, ticker):
        strategy = request.query_params.get('strategy', 'MACD').upper()
        capital = float(request.query_params.get('initial_capital', 100000))
        
        cache = MarketService.get_data()
        current_price = next((s.price for s in cache['stocks'] if s.ticker.upper() == ticker.upper()), 100.0)
        
        df = MarketService.get_predictor().get_data(ticker, current_price)
        from backtester import Backtester
        bt = Backtester(initial_capital=capital)
        results = bt.run_backtest(df.set_index('Date') if 'Date' in df.columns else df, strategy=strategy)
        return Response(MarketService.sanitize_json(results))

class PredictionView(APIView):
    def get(self, request, ticker):
        cache = MarketService.get_data()
        current_price = next((s.price for s in cache['stocks'] if s.ticker.upper() == ticker.upper()), 100.0)
        df = MarketService.get_predictor().get_data(ticker, current_price)
        
        trend = MarketService.get_predictor().analyze_trend(df)
        forecast = MarketService.get_predictor().predict_next_price(df)
        return Response(MarketService.sanitize_json({'trend': trend, 'price_forecast': forecast}))

class HistoryView(APIView):
    def get(self, request, ticker):
        cache = MarketService.get_data()
        current_price = next((s.price for s in cache['stocks'] if s.ticker.upper() == ticker.upper()), 100.0)
        df = MarketService.get_predictor().get_data(ticker, current_price)

        if df is None or df.empty:
            return Response({'error': 'No historical data found'}, status=404)

        df = df.copy()
        if 'Date' in df.columns:
            df['Date'] = df['Date'].astype(str)

        records = df.to_dict('records')
        return Response(MarketService.sanitize_json(records))


# ── Auth Endpoints ──────────────────────────────────────────────────────────

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email', '').strip().lower()
        password = request.data.get('password', '')
        telegram_id = request.data.get('telegram_id')

        if not email or not password:
            return Response({'error': 'Email and password required'}, status=400)
        if User.objects.filter(username=email).exists():
            return Response({'error': 'Account already exists'}, status=400)

        user = User.objects.create_user(username=email, email=email, password=password)
        profile = UserProfile.objects.create(user=user, telegram_id=telegram_id)

        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'tier': profile.tier,
        }, status=201)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email', '').strip().lower()
        password = request.data.get('password', '')
        user = authenticate(request, username=email, password=password)
        if not user:
            return Response({'error': 'Invalid credentials'}, status=401)

        profile, _ = UserProfile.objects.get_or_create(user=user)
        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'tier': profile.tier,
            'subscription_end': profile.subscription_end,
        })


class TelegramLoginView(APIView):
    """Passwordless login for Telegram users by telegram_id. Auto-creates account on first use."""
    permission_classes = [AllowAny]

    def post(self, request):
        telegram_id = str(request.data.get('telegram_id', ''))
        first_name = str(request.data.get('first_name', ''))
        if not telegram_id:
            return Response({'error': 'telegram_id required'}, status=400)
        try:
            profile = UserProfile.objects.select_related('user').get(telegram_id=telegram_id)
        except UserProfile.DoesNotExist:
            # Auto-create a User + UserProfile for this Telegram user on first login
            username = f"tg_{telegram_id}"
            user, _ = User.objects.get_or_create(
                username=username,
                defaults={'first_name': first_name, 'is_active': True},
            )
            profile, _ = UserProfile.objects.get_or_create(
                user=user,
                defaults={'telegram_id': telegram_id, 'tier': 'free'},
            )
            if not profile.telegram_id:
                profile.telegram_id = telegram_id
                profile.save()
        refresh = RefreshToken.for_user(profile.user)
        return Response({
            'access': str(refresh.access_token),
            'tier': profile.tier,
            'is_pro': profile.is_pro,
            'created': not profile.pk,
        })


class TelegramLinkView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        telegram_id = request.data.get('telegram_id')
        if not telegram_id:
            return Response({'error': 'telegram_id required'}, status=400)
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        profile.telegram_id = str(telegram_id)
        profile.save()
        return Response({'status': 'linked', 'telegram_id': telegram_id})


class PlanView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        return Response({
            'tier': profile.tier,
            'is_pro': profile.is_pro,
            'subscription_end': profile.subscription_end,
            'prices': TIER_PRICES,
        })


# ── Subscription / M-Pesa Endpoints ────────────────────────────────────────

class SubscribeInitiateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        tier = request.data.get('tier', 'pro').lower()
        phone = request.data.get('phone', '')

        if tier not in TIER_PRICES:
            return Response({'error': f'Invalid tier. Choose: {list(TIER_PRICES)}'}, status=400)
        if not phone:
            profile, _ = UserProfile.objects.get_or_create(user=request.user)
            phone = profile.mpesa_phone or ''
        if not phone:
            return Response({'error': 'M-Pesa phone number required'}, status=400)

        try:
            result = stk_push(phone, tier, request.user.id)
        except Exception as e:
            return Response({'error': f'STK Push failed: {e}'}, status=502)

        if result.get('ResponseCode') != '0':
            return Response({'error': result.get('ResponseDescription', 'STK Push failed')}, status=400)

        Subscription.objects.create(
            user=request.user,
            tier=tier,
            amount=TIER_PRICES[tier],
            mpesa_phone=phone,
            checkout_request_id=result.get('CheckoutRequestID'),
            merchant_request_id=result.get('MerchantRequestID'),
        )

        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        if not profile.mpesa_phone:
            profile.mpesa_phone = phone
            profile.save()

        return Response({
            'status': 'stk_sent',
            'message': f'Check your phone ({phone}) for the M-Pesa prompt.',
            'checkout_request_id': result.get('CheckoutRequestID'),
        })


class SubscribeCallbackView(APIView):
    """Daraja webhook — Safaricom calls this after payment completes."""
    permission_classes = [AllowAny]

    def post(self, request):
        body = request.data.get('Body', {})
        callback = body.get('stkCallback', {})
        checkout_id = callback.get('CheckoutRequestID')
        result_code = callback.get('ResultCode')

        sub = Subscription.objects.filter(checkout_request_id=checkout_id).first()
        if not sub:
            return Response({'ResultCode': 0, 'ResultDesc': 'Unknown'})

        if result_code == 0:
            sub.status = Subscription.STATUS_ACTIVE
            sub.activated_at = timezone.now()
            sub.save()

            profile, _ = UserProfile.objects.get_or_create(user=sub.user)
            profile.tier = sub.tier
            profile.subscription_end = timezone.now() + timedelta(days=30)
            profile.save()
        else:
            sub.status = Subscription.STATUS_FAILED
            sub.save()

        return Response({'ResultCode': 0, 'ResultDesc': 'Accepted'})
