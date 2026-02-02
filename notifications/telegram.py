from __future__ import annotations

from django.conf import settings
#from notifications.telegram import send_telegram_message


def send_telegram_message(*, user, text: str) -> bool:
    """
    Minimal stub so imports work.
    Later you can wire real Telegram delivery using python-telegram-bot.
    """
    # If you haven't configured telegram yet, just skip safely
    if not getattr(settings, "TELEGRAM_ENABLED", False):
        return False

    # If you later store telegram chat_id on user/profile, fetch it here:
    chat_id = getattr(user, "telegram_chat_id", None)
    bot_token = getattr(settings, "TELEGRAM_BOT_TOKEN", "")

    if not (chat_id and bot_token):
        return False

    # Real sending will be added later
    return True
