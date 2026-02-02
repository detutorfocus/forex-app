# accounts/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import TraderProfile

@receiver(post_save, sender=User)
def create_trader_profile(sender, instance, created, **kwargs):
    if created:
        TraderProfile.objects.create(user=instance)
