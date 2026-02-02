import hashlib
import hmac
import time
from typing import Dict, Tuple

from django.conf import settings


def verify_telegram_auth(data: Dict[str, str], max_age_seconds: int = 300) -> Tuple[bool, str]:
    """
    Verifies Telegram login widget auth data.
    Telegram docs: build data_check_string, compute HMAC-SHA256 with secret=sha256(bot_token).
    """
    if "hash" not in data:
        return False, "Missing hash"

    tg_hash = data["hash"]
    auth_date = int(data.get("auth_date", "0") or "0")
    if not auth_date:
        return False, "Missing auth_date"

    # prevent replay
    if int(time.time()) - auth_date > max_age_seconds:
        return False, "Auth data expired"

    pairs = []
    for k, v in data.items():
        if k == "hash":
            continue
        pairs.append(f"{k}={v}")
    pairs.sort()
    data_check_string = "\n".join(pairs)

    bot_token = getattr(settings, "TELEGRAM_BOT_TOKEN", "")
    if not bot_token:
        return False, "Server misconfigured"

    secret_key = hashlib.sha256(bot_token.encode("utf-8")).digest()
    computed_hash = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(computed_hash, tg_hash):
        return False, "Invalid signature"

    return True, ""
