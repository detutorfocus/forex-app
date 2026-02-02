# trading/utils.py
import json
from decimal import Decimal
from datetime import datetime, date
from .mt5.service import MT5Service


def sync_mt5_account(trader_profile):
    svc = MT5Service()
    info = svc.get_account_info()  # <-- must return dict like {"balance":..., "equity":...}

    if not info:
        return False

    trader_profile.mt5_balance = info.get("balance")
    trader_profile.mt5_equity = info.get("equity")
    trader_profile.save(update_fields=["mt5_balance", "mt5_equity"])
    return True

def json_safe(obj):
    def default(o):
        if isinstance(o, (datetime, date)):
            return o.isoformat()
        if isinstance(o, Decimal):
            return float(o)
        if hasattr(o, "_asdict"):
            return o._asdict()
        return str(o)


    # Convert to plain JSON-able Python types
    return json.loads(json.dumps(obj, default=default))
