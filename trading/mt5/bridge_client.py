import os
import requests

BRIDGE_URL = os.getenv("MT5_BRIDGE_URL", "http://127.0.0.1:9001")

def bridge_post(path: str, payload: dict, timeout: int = 20):
    r = requests.post(f"{BRIDGE_URL}{path}", json=payload, timeout=timeout)
    r.raise_for_status()
    return r.json()
