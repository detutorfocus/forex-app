import os
import threading
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import MetaTrader5 as mt5

BASE_DIR = os.getenv("MT5_USER_BASE_DIR", r"C:\mt5_users")
TERMINAL_PATH = os.getenv("MT5_TERMINAL_PATH", r"C:\Program Files\MetaTrader 5\terminal64.exe")

app = FastAPI()
locks: dict[int, threading.Lock] = {}

def _lock(user_id: int) -> threading.Lock:
    if user_id not in locks:
        locks[user_id] = threading.Lock()
    return locks[user_id]

def user_dir(user_id: int) -> str:
    d = os.path.join(BASE_DIR, str(user_id))
    os.makedirs(d, exist_ok=True)
    return d

class ConnectIn(BaseModel):
    user_id: int
    login: int
    server: str
    password: str

@app.post("/connect")
def connect(inp: ConnectIn):
    with _lock(inp.user_id):
        # Important: shutdown between sessions in SAME process
        try:
            mt5.shutdown()
        except Exception:
            pass

        # For true isolation, you’ll eventually run a process-per-user.
        # This minimal version serializes per user and uses separate dirs for future portability.
        ok = mt5.initialize(
            path=TERMINAL_PATH,
            login=inp.login,
            password=inp.password,
            server=inp.server,
        )
        if not ok:
            raise HTTPException(status_code=400, detail=f"MT5 init failed: {mt5.last_error()}")

        info = mt5.account_info()
        return {"ok": True, "account": info._asdict() if info else None}
