from django.db import models
from django.contrib.auth.models import User
# Create your models here.
from django.conf import settings
from security.crypto import encrypt_str, decrypt_str

class TraderProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete= models.CASCADE,
        related_name= "trader_profile"
    )
    #mt5 acct detail
    mt5_login = models.BigIntegerField(null=True, blank=True)
    mt5_server = models.CharField(max_length=100, null=True, blank=True)
    mt5_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    mt5_equity = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)

    # Risk Management
    risk_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=1.00)
    max_daily_loss = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    # Status
    is_verified = models.BooleanField(default=False)
    is_active_trader = models.BooleanField(default=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - MT5 Trader"




class MT5Account(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="mt5_account")
    login = models.BigIntegerField()
    server = models.CharField(max_length=120)

    #TODO: encrypt at rest in production
    password = models.CharField(max_length=255)

    password_enc = models.TextField()  # encrypted blob

    is_active = models.BooleanField(default=True)
    last_connected_at = models.DateTimeField(null=True, blank=True)

    def set_password(self, raw: str):
        self.password_enc = encrypt_str(raw)

    def get_password(self) -> str:
        return decrypt_str(self.password_enc)

    is_active = models.BooleanField(default=True)
    last_connected_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"MT5Account<{self.user_id}> {self.server} {self.login}"


class BrokerPortal(models.Model):
    name = models.CharField(max_length=120, unique=True)
    server_keywords = models.JSONField(default=list, blank=True)  # ["Exness", "ICMarkets", ...]
    withdraw_url = models.URLField(blank=True, default="")
    portal_url = models.URLField(blank=True, default="")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
