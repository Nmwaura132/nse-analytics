from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class UserProfile(models.Model):
    TIER_FREE = 'free'
    TIER_PRO = 'pro'
    TIER_CLUB = 'club'
    TIER_CHOICES = [(TIER_FREE, 'Free'), (TIER_PRO, 'Pro'), (TIER_CLUB, 'Club')]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    telegram_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    tier = models.CharField(max_length=10, choices=TIER_CHOICES, default=TIER_FREE)
    subscription_end = models.DateTimeField(null=True, blank=True)
    mpesa_phone = models.CharField(max_length=15, null=True, blank=True)
    bonus_requests = models.IntegerField(default=0)
    bot_portfolio_consent = models.BooleanField(default=False)
    consent_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_pro(self):
        if self.tier in (self.TIER_PRO, self.TIER_CLUB):
            return self.subscription_end and self.subscription_end > timezone.now()
        return False

    @property
    def is_club(self):
        return self.tier == self.TIER_CLUB and self.subscription_end and self.subscription_end > timezone.now()

    def __str__(self):
        return f"{self.user.email} [{self.tier}]"


class Subscription(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_ACTIVE = 'active'
    STATUS_FAILED = 'failed'
    STATUS_CHOICES = [(STATUS_PENDING, 'Pending'), (STATUS_ACTIVE, 'Active'), (STATUS_FAILED, 'Failed')]

    TIER_CHOICES = UserProfile.TIER_CHOICES

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    tier = models.CharField(max_length=10, choices=TIER_CHOICES)
    amount = models.IntegerField()  # KES
    mpesa_phone = models.CharField(max_length=15)
    checkout_request_id = models.CharField(max_length=100, null=True, blank=True)
    merchant_request_id = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    activated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.tier} - {self.status}"


class Trade(models.Model):
    user_id = models.CharField(max_length=100, default='1')
    ticker = models.CharField(max_length=20)
    qty = models.FloatField(default=0.0)
    avg_cost = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'trades'
        unique_together = ('user_id', 'ticker')

    def __str__(self):
        return f"{self.user_id} - {self.ticker}: {self.qty} @ {self.avg_cost}"


class DailyUsage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_usage')
    date = models.DateField()
    count = models.IntegerField(default=0)

    class Meta:
        unique_together = ('user', 'date')

    def __str__(self):
        return f"{self.user.username} {self.date}: {self.count}"


class TopUp(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_ACTIVE = 'active'
    STATUS_FAILED = 'failed'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_ACTIVE, 'Active'),
        (STATUS_FAILED, 'Failed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='topups')
    requests = models.IntegerField()
    amount = models.IntegerField()
    checkout_request_id = models.CharField(max_length=100, null=True, blank=True)
    merchant_request_id = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} +{self.requests} reqs KES {self.amount} [{self.status}]"
