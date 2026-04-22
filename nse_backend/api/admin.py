from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Trade, UserProfile, Subscription


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('email', 'tier_badge', 'telegram_id', 'mpesa_phone', 'subscription_status', 'created_at')
    list_filter = ('tier',)
    search_fields = ('user__email', 'telegram_id', 'mpesa_phone')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)

    def email(self, obj):
        return obj.user.email
    email.short_description = 'Email'

    def tier_badge(self, obj):
        colors = {'free': '#6c757d', 'pro': '#0d6efd', 'club': '#198754'}
        color = colors.get(obj.tier, '#6c757d')
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:4px;font-weight:bold">{}</span>',
            color, obj.tier.upper()
        )
    tier_badge.short_description = 'Tier'

    def subscription_status(self, obj):
        if not obj.subscription_end:
            return '—'
        if obj.subscription_end > timezone.now():
            days = (obj.subscription_end - timezone.now()).days
            return format_html('<span style="color:green">✓ Active ({} days left)</span>', days)
        return format_html('<span style="color:red">✗ Expired</span>')
    subscription_status.short_description = 'Subscription'


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'tier', 'amount_display', 'status_badge', 'mpesa_phone', 'created_at', 'activated_at')
    list_filter = ('status', 'tier')
    search_fields = ('user__email', 'mpesa_phone', 'checkout_request_id')
    readonly_fields = ('checkout_request_id', 'merchant_request_id', 'created_at', 'activated_at')
    ordering = ('-created_at',)

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'

    def amount_display(self, obj):
        return f'KES {obj.amount:,}'
    amount_display.short_description = 'Amount'

    def status_badge(self, obj):
        colors = {'pending': '#ffc107', 'active': '#198754', 'failed': '#dc3545'}
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:4px">{}</span>',
            color, obj.status.upper()
        )
    status_badge.short_description = 'Status'


@admin.register(Trade)
class TradeAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'ticker', 'qty', 'avg_cost', 'current_value', 'created_at')
    list_filter = ('ticker',)
    search_fields = ('user_id', 'ticker')
    ordering = ('-created_at',)

    def current_value(self, obj):
        return f'KES {obj.qty * obj.avg_cost:,.2f}'
    current_value.short_description = 'Est. Value'
