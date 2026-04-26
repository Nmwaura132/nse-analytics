from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # Auth
    path('auth/register', views.RegisterView.as_view()),
    path('auth/login', views.LoginView.as_view()),
    path('auth/refresh', TokenRefreshView.as_view()),
    path('auth/telegram-link', views.TelegramLinkView.as_view()),
    path('auth/telegram-login', views.TelegramLoginView.as_view()),

    # Subscription
    path('plan', views.PlanView.as_view()),
    path('subscribe/initiate', views.SubscribeInitiateView.as_view()),
    path('subscribe/callback', views.SubscribeCallbackView.as_view()),

    # Market (free)
    path('stocks', views.StockListView.as_view()),
    path('stock/<str:ticker>', views.StockDetailView.as_view()),
    path('refresh', views.RefreshDataView.as_view()),

    # Portfolio (free)
    path('portfolio', views.PortfolioListView.as_view()),
    path('portfolio/add', views.AddTradeView.as_view()),
    path('portfolio/remove', views.RemoveTradeView.as_view()),
    path('portfolio/consent', views.PortfolioConsentView.as_view()),

    path('notifications', views.NotificationView.as_view()),

    # Pro features
    path('portfolio/optimize', views.OptimizePortfolioView.as_view()),
    path('backtest/<str:ticker>', views.BacktestView.as_view()),
    path('predict/<str:ticker>', views.PredictionView.as_view()),
    path('history/<str:ticker>', views.HistoryView.as_view()),

    # Rate limiting
    path('rate-limit/status/<str:telegram_id>', views.RateLimitStatusView.as_view()),
    path('rate-limit/consume/<str:telegram_id>', views.RateLimitConsumeView.as_view()),

    # Top-up
    path('topup/initiate', views.TopUpInitiateView.as_view()),
    path('topup/callback', views.TopUpCallbackView.as_view()),

    # Admin events (called by hermes gateway)
    path('admin/notify', views.AdminNotifyView.as_view()),

    # Admin stats (Django superusers only)
    path('admin/stats', views.AdminStatsView.as_view()),
]
