from django.urls import path
from . import views

urlpatterns = [
    path('stocks', views.StockListView.as_view()),
    path('stock/<str:ticker>', views.StockDetailView.as_view()),
    path('refresh', views.RefreshDataView.as_view()),
    
    path('portfolio', views.PortfolioListView.as_view()),
    path('portfolio/add', views.AddTradeView.as_view()),
    path('portfolio/remove', views.RemoveTradeView.as_view()),
    path('portfolio/optimize', views.OptimizePortfolioView.as_view()),
    
    path('notifications', views.NotificationView.as_view()),
    
    path('backtest/<str:ticker>', views.BacktestView.as_view()),
    path('predict/<str:ticker>', views.PredictionView.as_view()),
    path('history/<str:ticker>', views.HistoryView.as_view()),
]
