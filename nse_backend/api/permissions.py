"""
Subscription tier gating for API views and Telegram bot commands.
"""
from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied
from django.utils import timezone


PRO_ENDPOINTS = {
    'predict', 'backtest', 'optimize', 'history',
}

UPGRADE_MSG = (
    "⭐ *This is a Pro feature.*\n\n"
    "Upgrade to NSE Pro (KES 500/month) to unlock:\n"
    "• ML price predictions\n"
    "• Backtesting engine\n"
    "• Portfolio optimizer\n"
    "• AI stock analysis\n\n"
    "Send /subscribe to upgrade."
)

PRO_BOT_COMMANDS = {
    '/predict', '/analyze', '/ask', '/portfolio',
    '/optimize', '/backtest', '/chart', '/forecast', '/alert',
    '/myalerts', '/delalert', '/pchart',
}


class IsPro(BasePermission):
    """DRF permission — requires active Pro or Club subscription."""
    message = "Pro subscription required. Visit /api/subscribe/initiate to upgrade."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        try:
            profile = request.user.profile
            return profile.is_pro
        except Exception:
            return False


def check_telegram_tier(user_profile, command: str) -> tuple[bool, str]:
    """
    Returns (allowed, message).
    Call before processing any Telegram command.
    """
    cmd = command.split()[0].lower().split('@')[0]
    if cmd not in PRO_BOT_COMMANDS:
        return True, ""
    if user_profile and user_profile.is_pro:
        return True, ""
    return False, UPGRADE_MSG


def get_profile_for_telegram(telegram_id: str):
    """Fetch UserProfile by Telegram ID. Returns None if not linked."""
    try:
        from api.models import UserProfile
        return UserProfile.objects.select_related('user').get(telegram_id=str(telegram_id))
    except Exception:
        return None
