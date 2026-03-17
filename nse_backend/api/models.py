from django.db import models

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
