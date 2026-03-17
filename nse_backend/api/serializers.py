from rest_framework import serializers
from .models import Trade

class TradeSerializer(serializers.ModelSerializer):
    """Serializer for Trade model instances."""
    pnl = serializers.FloatField(read_only=True)
    pnl_pct = serializers.FloatField(read_only=True)
    current_price = serializers.FloatField(read_only=True)

    class Meta:
        model = Trade
        fields = ['id', 'user_id', 'ticker', 'qty', 'avg_cost', 'current_price', 'pnl', 'pnl_pct', 'created_at', 'updated_at']

class MarketSummarySerializer(serializers.Serializer):
    """Serializer for overall market summary stats."""
    total = serializers.IntegerField()
    gainers_count = serializers.IntegerField()
    losers_count = serializers.IntegerField()
    unchanged_count = serializers.IntegerField()
    buy_candidates_count = serializers.IntegerField()

class NotificationSerializer(serializers.Serializer):
    """Serializer for notification messages."""
    id = serializers.IntegerField(read_only=True)
    timestamp = serializers.CharField(read_only=True)
    message = serializers.CharField(required=True)
    type = serializers.CharField(default='info')
