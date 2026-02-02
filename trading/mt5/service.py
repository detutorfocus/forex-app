import re
from distutils.log import info
import MetaTrader5 as mt5
from datetime import datetime
import time

from typing_extensions import Self
from trading.audit import audit_event, AuditCtx
from trading.models import Trade, TradeAuditEvent
#DEFAULT_MT5_PATH = r"C:\Program Files\MetaTrader 5 EXNESS\terminal64.exe"
DEFAULT_MT5_PATH = r"C:\Program Files\MetaTrader 5\terminal64.exe"
from security.permissions import RequiresReauth
import os
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .market_broadcast import broadcast_candle



"""def ensure_symbol(symbol: str):
    info = mt5.symbol_info(symbol)
    if info is None:
         raise ValueError(f"Symbol {symbol} not found")

    if not info.visible:
        mt5.symbol_select(symbol, True)"""


TIMEFRAMES = {
    "M1": mt5.TIMEFRAME_M1,
    "M5": mt5.TIMEFRAME_M5,
    "M15": mt5.TIMEFRAME_M15,
    "M30": mt5.TIMEFRAME_M30,
    "H1": mt5.TIMEFRAME_H1,
    "H4": mt5.TIMEFRAME_H4,
    "D1": mt5.TIMEFRAME_D1,
}

class MT5Service:
    DEFAULT_MT5_PATH = r"C:\Program Files\MetaTrader 5\terminal64.exe"

    def __init__(self, path: str | None = None):
        self.connected = False
        self.path = path or self.DEFAULT_MT5_PATH
    #MAGIC = 900001
    COMMENT = "SniperATR"

    def place_market_order(
            self,
            trade,
            symbol: str,
            side: str,
            lot: float,
            sl: float = None,
            tp: float = None,
            comment="",
            max_slippage_pips: float = 2.0,
            *,
            ctx: AuditCtx | None = None,
            **kwargs
    ) -> dict:
        ctx = ctx or AuditCtx()
        self._log(trade, TradeAuditEvent.EventType.VALIDATION_OK, {"symbol": symbol, "side": side, "lot": float(lot)},
                  ctx)

        """
        Places a market order using broker-supported filling mode fallback.
        Returns a dict: {"ok": bool, ...}
        """

        # 1) Ensure MT5 connection/session
        self._ensure_connected()

        # 2) Resolve + ensure symbol is visible/selectable
        resolved = self.resolve_symbol(symbol)
        if not resolved:
            return {"ok": False, "error": "Symbol not found", "symbol": symbol}

        self._log(trade, TradeAuditEvent.EventType.MT5_CONNECT_OK, {}, ctx)

        symbol = resolved
        try:
            self.ensure_symbol(symbol)
        except Exception as e:
            return {"ok": False, "error": str(e), "symbol": symbol}

        # 3) Get tick price
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            return {"ok": False, "error": "No tick data", "symbol": symbol, "last_error": mt5.last_error()}

        side_l = (side or "").strip().lower()
        if side_l not in ("buy", "sell"):
            return {"ok": False, "error": "Invalid side (use 'buy' or 'sell')", "symbol": symbol, "side": side}

        price = tick.ask if side_l == "buy" else tick.bid
        if not price:
            return {"ok": False, "error": "No price for side", "symbol": symbol, "side": side_l}

        order_type = mt5.ORDER_TYPE_BUY if side_l == "buy" else mt5.ORDER_TYPE_SELL

        # 4) Compute deviation (optional)
        deviation_points = self._compute_slippage_points(symbol, max_slippage_pips)

        # 5) Build request (NO manual order_send here)
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": float(lot),
            "type": order_type,
            "price": float(price),
            "deviation": int(deviation_points),
            #"magic": int(self.MAGIC),
            "comment": self.COMMENT,
        }

        if sl is not None:
            request["sl"] = float(sl)
        if tp is not None:
            request["tp"] = float(tp)

        # 6) ONLY RETURN should be this:
        return self._send_with_supported_filling(request)

    def _audit_ctx_from_request(request) -> AuditCtx:
        user = getattr(request, "user", None)
        actor_id = user.id if user and user.is_authenticated else None
        ip = request.META.get("REMOTE_ADDR")
        ua = request.META.get("HTTP_USER_AGENT")
        return AuditCtx(actor_id=actor_id, ip=ip, user_agent=ua)



    # --- helpers you already have / should have ---

    def _compute_slippage_points(self, symbol: str, max_slippage_pips: float) -> int:
        info = mt5.symbol_info(symbol)
        if info is None:
            return 20  # fallback
        point = info.point or 0.0
        if point <= 0:
            return 20
        # for many FX symbols: 1 pip = 10 points (if digits=5), for digits=3 same idea
        # this is safe enough as a general conversion:
        pip_value = point * 10 if info.digits in (3, 5) else point
        points = (max_slippage_pips * pip_value) / point
        return max(1, int(round(points)))


    def resolve_symbol(self, symbol: str):
        raw = (symbol or "").strip()
        if not raw:
            return None

        # try exact first
        if mt5.symbol_info(raw) is not None:
            return raw

        up = raw.upper()

        # common aliases you can expand anytime
        aliases = {
            "XAUUSD": ["XAUUSD", "GOLD", "XAUUSDm", "GOLDm"],
            "GOLD":   ["GOLD", "XAUUSD", "GOLDm", "XAUUSDm"],
            "GBPUSD": ["GBPUSD", "GBPUSDm"],
            "EURUSD": ["EURUSD", "EURUSDm"],
        }

        for cand in aliases.get(up, []):
            if mt5.symbol_info(cand) is not None:
                return cand

        # last resort: search ALL broker symbols and pick best match
        symbols = mt5.symbols_get()
        if not symbols:
            return None

        # normalize
        def norm(s: str) -> str:
            return re.sub(r"[^A-Z0-9]", "", (s or "").upper())

        target = norm(up)

        # match if target appears in name (handles suffix like XAUUSDm, GBPUSD.i)
        matches = [s.name for s in symbols if target in norm(s.name)]

        # also allow GOLD<->XAUUSD
        if not matches and up in ("XAUUSD", "GOLD"):
            matches = [s.name for s in symbols if "XAU" in s.name.upper() or "GOLD" in s.name.upper()]

        return matches[0] if matches else None

    # --- connection helpers ---
    def _ensure_initialized(self) -> bool:
            # Don’t initialize repeatedly if already connected
        if mt5.terminal_info() is not None:
            return True
        return mt5.initialize()

    def ensure_symbol(self, symbol: str) -> str:
        resolved = self.resolve_symbol(symbol) or symbol
        info = mt5.symbol_info(resolved)
        if info is None:
            raise ValueError(f"Symbol not found: {symbol} (resolved={resolved})")

        if not info.visible:
            ok = mt5.symbol_select(resolved, True)
            if not ok:
                err = mt5.last_error()
                raise ValueError(f"Symbol not selectable: {resolved}. mt5.last_error={err}")

        # Optional: trading allowed check
        if hasattr(info, "trade_mode") and info.trade_mode == 0:
            raise ValueError(f"Trading disabled for symbol: {resolved} (trade_mode=0)")

        return resolved

    def _get_tick_with_retry(self, symbol: str, retries: int = 10, delay: float = 0.2):
        tick = None
        for _ in range(retries):
            tick = mt5.symbol_info_tick(symbol)
            if tick and tick.ask and tick.bid:
                return tick
            time.sleep(delay)
            return None

    def _compute_slippage_points(self, symbol: str, max_slippage_pips: float) -> int:
        info = mt5.symbol_info(symbol)
        if info is None:
            return 20  # fallback
            # point = smallest price step
            # pip -> points conversion depends on digits; safe approach:
            # 1 pip ~ 10 points for 5-digit FX, but metals vary.
            # We'll approximate using digits:
        digits = getattr(info, "digits", 5)
            # If digits >= 3: use pip = 10 points; else pip = 1 point
        pip_in_points = 10 if digits >= 3 else 1
        points = int(max(1, round(max_slippage_pips * pip_in_points)))
        return points

    def _pick_filling_mode(self, symbol: str) -> int:
        """
        Returns a safe filling mode for this broker/symbol.
        Prefers IOC then FOK then RETURN. Falls back to IOC.
        """
        info = mt5.symbol_info(symbol)

        # Some builds use "filling_mode", others use "filling_mode" differently.
        # We'll handle safely.
        fm = None
        if info is not None:
            if hasattr(info, "filling_mode"):
                fm = info.filling_mode

        candidates = [
            mt5.ORDER_FILLING_IOC,
            mt5.ORDER_FILLING_FOK,
            mt5.ORDER_FILLING_RETURN,
        ]

        if fm in candidates:
            return fm

        # fallback
        return mt5.ORDER_FILLING_IOC

        # Keep your resolve_symbol if you already wrote it

    def connect(self, login: int | None = None, password: str | None = None, server: str | None = None):
        """
        If login/password/server provided -> initializes MT5 and logs into that account.
        If not provided -> just initializes the terminal.
        """
        # shutdown any previous session cleanly (important when switching accounts)
        try:
            mt5.shutdown()
        except Exception:
            pass

        ok = mt5.initialize(
            path=self.path,
            login=login,
            password=password,
            server=server,
        )

        if not ok:
            raise ConnectionError(f"MT5 initialization failed -> {mt5.last_error()}")

        self.connected = True
        return True
        # ===============================
        # STAGE 5 – NEW METHODS (ADD BELOW)
        # ===============================

    SYMBOL_ALIASES = {
        "XAUUSD": ["XAUUSD", "XAUUSDm", "XAUUSD.i", "GOLD", "GOLDm"],
        "GBPUSD": ["GBPUSD", "GBPUSDm", "GBPUSD.i"],
        "EURUSD": ["EURUSD", "EURUSDm", "EURUSD.i"],
    }

    def shutdown(self):
        #mt5.shutdown()
        self.connected = False

    def get_symbol_tick(self, symbol: str):
        if not self.connected:
            self.connect()

        if not mt5.symbol_select(symbol, True):
            raise ValueError(f"Symbol {symbol} not found")

        tick = mt5.symbol_info_tick(symbol)

        if tick is None:
            raise ValueError("Tick data unavailable")

        return {
            "symbol": symbol,
            "bid": tick.bid,
            "ask": tick.ask,
            "last": tick.last,
            "time": datetime.fromtimestamp(tick.time).isoformat()
        }

    def resolve_symbol(self, symbol: str) -> str | None:
        """
        Returns a broker-available symbol for the requested symbol.
        Example: XAUUSD -> XAUUSDm / GOLD / GOLDm
        """

        if not symbol:
            return None

        raw = symbol.strip().upper()

        # 1) Exact match
        info = mt5.symbol_info(raw)
        if info is not None:
            mt5.symbol_select(raw, True)
            return raw

        # 2) Common aliases (expand anytime)
        aliases = {
            "XAUUSD": ["XAUUSD", "GOLD", "XAUUSDm", "GOLDm", "XAUUSD.i", "XAUUSD#", "GOLD.i"],
            "XAGUSD": ["XAGUSD", "SILVER", "XAGUSDm", "SILVERm"],
        }

        candidates = aliases.get(raw, [raw])

        # 3) Try direct candidates
        for cand in candidates:
            inf = mt5.symbol_info(cand)
            if inf is not None:
                mt5.symbol_select(cand, True)
                return cand

        # 4) Fuzzy search across ALL broker symbols
        all_syms = mt5.symbols_get()
        if not all_syms:
            return None

        # normalize: keep only letters/numbers so "XAUUSD.m" matches "XAUUSD"
        def norm(s: str) -> str:
            return re.sub(r"[^A-Z0-9]", "", s.upper())

        target = norm(raw)

        # pick best match that contains target
        matches = [s.name for s in all_syms if target in norm(s.name)]

        # preference: ones starting with target
        matches.sort(key=lambda n: (0 if norm(n).startswith(target) else 1, len(n)))

        if matches:
            best = matches[0]
            mt5.symbol_select(best, True)
            return best

        return None



    def get_open_positions(self, symbol: str = None):
        if symbol:
            return mt5.positions_get(symbol=symbol) or []
        return mt5.positions_get() or []

    def get_position_by_ticket(self, ticket: int):
        positions = mt5.positions_get(ticket=ticket)
        if not positions:
            return None
        return positions[0]

    def close_position_by_ticket(
            self,
            position_ticket: int,
            deviation: int = 20,
            magic: int = 123456,
            comment: str = "api-close",
    ) -> dict:

        if not mt5.initialize():
            return {"error": "MT5 initialize failed", "status": 500, "last_error": mt5.last_error()}

        pos_list = mt5.positions_get(ticket=position_ticket)
        if not pos_list:
            mt5.shutdown()
            return {"error": f"Position {position_ticket} not found", "status": 404}

        pos = pos_list[0]
        symbol = pos.symbol

        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            #mt5.shutdown()
            return {"error": f"No tick for {symbol}", "status": 404}

        # opposite side to close
        if pos.type == mt5.POSITION_TYPE_BUY:
            order_type = mt5.ORDER_TYPE_SELL
            price = tick.bid
        else:
            order_type = mt5.ORDER_TYPE_BUY
            price = tick.ask

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "position": int(pos.ticket),
            "volume": float(pos.volume),
            "type": order_type,
            "price": float(price),
            "deviation": int(deviation),
            "magic": int(magic),
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
            # type_filling will be set by _send_with_supported_filling
        }

        #result, used_filling = self._send_with_supported_filling(request)

    #@staticmethod



    def _send_with_supported_filling(self, request: dict):
        FILLING_CANDIDATES = [
            mt5.ORDER_FILLING_FOK,
            mt5.ORDER_FILLING_IOC,
            mt5.ORDER_FILLING_RETURN,
        ]

        last_result = None
        last_filling = None

        for filling in FILLING_CANDIDATES:
            req = dict(request)
            req["type_filling"] = filling

            result = mt5.order_send(req)
            last_result = result
            last_filling = filling

            # success
            if result is not None and result.retcode == mt5.TRADE_RETCODE_DONE:
                return result, filling

            # unsupported filling => try next
            if result is not None and result.retcode in (
                    mt5.TRADE_RETCODE_INVALID_FILL,
                    mt5.TRADE_RETCODE_INVALID,
            ):
                continue

        return last_result, last_filling

    def close_position_by_ticket(
            self,
            position_ticket: int,
            deviation: int = 20,
            magic: int = 123456,
            comment: str = "api-close",
    ):
        payload = {
            "requested_position_ticket": int(position_ticket),
            "mt5": None,
            "status": 500,
        }

        try:
            if not mt5.initialize():
                payload["error"] = "MT5 initialize failed"
                payload["last_error"] = mt5.last_error()
                return payload

            pos_list = mt5.positions_get(ticket=int(position_ticket))
            if not pos_list:
                payload["error"] = f"Position {position_ticket} not found"
                payload["status"] = 404
                return payload

            pos = pos_list[0]
            symbol = pos.symbol

            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                payload["error"] = f"No tick for {symbol}"
                payload["status"] = 404
                return payload

            # opposite side to close
            if pos.type == mt5.POSITION_TYPE_BUY:
                order_type = mt5.ORDER_TYPE_SELL
                price = tick.bid
            else:
                order_type = mt5.ORDER_TYPE_BUY
                price = tick.ask

            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "position": int(pos.ticket),
                "volume": float(pos.volume),
                "type": order_type,
                "price": float(price),
                "deviation": int(deviation),
                "magic": int(magic),
                "comment": comment,
                "type_time": mt5.ORDER_TIME_GTC,
            }

            result, used_filling = self._send_with_supported_filling(request)

            payload["used_filling"] = int(used_filling) if used_filling is not None else None

            if result is None:
                payload["error"] = "order_send returned None"
                payload["last_error"] = mt5.last_error()
                payload["status"] = 500
                return payload

            payload["mt5"] = {
                "retcode": int(result.retcode),
                "order": int(getattr(result, "order", 0) or 0),
                "deal": int(getattr(result, "deal", 0) or 0),
                "price": float(getattr(result, "price", 0.0) or 0.0),
                "comment": str(getattr(result, "comment", "")),
                "request_id": int(getattr(result, "request_id", 0) or 0),
            }

            if result.retcode != mt5.TRADE_RETCODE_DONE:
                payload["error"] = "Close failed"
                payload["details"] = payload["mt5"]["comment"]
                payload["status"] = 400
                return payload

            payload["status"] = 200
            payload["message"] = "Position closed"
            return payload

        except Exception as e:
            payload["error"] = "Exception in close_position_by_ticket"
            payload["details"] = str(e)
            payload["status"] = 500
            return payload

        finally:
            try:
                mt5.shutdown()
            except Exception:
                pass

    def modify_position_sl_tp(self, ticket: int, sl: float = None, tp: float = None):
        pos = self.get_position_by_ticket(ticket)
        if pos is None:
            raise ValueError(f"Position with ticket {ticket} not found")

        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "position": ticket,
            "symbol": pos.symbol,
            "sl": sl if sl is not None else pos.sl,
            "tp": tp if tp is not None else pos.tp,
        }

        result = mt5.order_send(request)
        if result is None:
            raise RuntimeError("order_send returned None (MT5 not ready?)")

        if result.retcode != mt5.TRADE_RETCODE_DONE:
            raise RuntimeError(f"Modify SL/TP failed: {result.comment}")

        return {"ticket": ticket, "result": "modified", "retcode": result.retcode}

    def close_all_positions(self):
        positions = mt5.positions_get() or []
        closed = []
        errors = []

        for p in positions:
            try:
                closed.append(self.close_position(int(p.ticket)))
            except Exception as e:
                errors.append({"ticket": int(p.ticket), "error": str(e)})

        return {"closed": closed, "errors": errors, "count": len(positions)}

    def list_positions(self, symbol: str = None):
        import MetaTrader5 as mt5

        if not mt5.initialize():
            raise RuntimeError("MT5 initialization failed")

        positions = mt5.positions_get(symbol=symbol) if symbol else mt5.positions_get()
        positions = positions or []

        data = []
        for p in positions:
            data.append({
                "ticket": p.ticket,
                "symbol": p.symbol,
                "type": "buy" if p.type == mt5.POSITION_TYPE_BUY else "sell",
                "volume": float(p.volume),
                "price_open": float(p.price_open),
                "sl": float(p.sl),
                "tp": float(p.tp),
                "profit": float(p.profit),
                "time": int(p.time),
                "magic": int(p.magic),
                "comment": str(p.comment),
            })

        #mt5.shutdown()
        return data

    def list_orders(self, symbol: str = None):
        import MetaTrader5 as mt5

        if not mt5.initialize():
            raise RuntimeError("MT5 initialization failed")

        orders = mt5.orders_get(symbol=symbol) if symbol else mt5.orders_get()
        orders = orders or []

        data = []
        for o in orders:
            data.append({
                "ticket": o.ticket,
                "symbol": o.symbol,
                "type": int(o.type),
                "volume_initial": float(o.volume_initial),
                "price_open": float(o.price_open),
                "sl": float(o.sl),
                "tp": float(o.tp),
                "time_setup": int(o.time_setup),
                "magic": int(o.magic),
                "comment": str(o.comment),
            })

        #mt5.shutdown()
        return data

    def _send_with_supported_filling(self, request: dict) -> dict:
        info = mt5.symbol_info(request["symbol"])
        if info is None:
            return {"ok": False, "error": f"Symbol not found: {request['symbol']}"}

        # Try the most common filling modes
        candidates = [
            mt5.ORDER_FILLING_IOC,
            mt5.ORDER_FILLING_FOK,
            mt5.ORDER_FILLING_RETURN,
        ]

        last = None
        for fill in candidates:
            req = dict(request)
            req["type_filling"] = fill

            res = mt5.order_send(req)
            last = res

            if res is not None and res.retcode in (mt5.TRADE_RETCODE_DONE, mt5.TRADE_RETCODE_PLACED):
                return {"ok": True, "retcode": res.retcode, "comment": res.comment, "result": res._asdict()}

            # If it failed for a reason other than filling mode, stop early
            if res is not None and "filling" not in (res.comment or "").lower():
                break

        # failed all candidates
        if last is None:
            return {"ok": False, "error": "order_send returned None", "last_error": mt5.last_error()}

        return {"ok": False, "retcode": last.retcode, "comment": last.comment, "result": last._asdict()}

    def _get_tick_with_retry(self, symbol: str, retries: int = 10, delay: float = 0.2):
        tick = None
        for _ in range(retries):
            tick = mt5.symbol_info_tick(symbol)
            if tick and tick.ask and tick.bid:
                return tick
            time.sleep(delay)
        return None

    def _compute_slippage_points(self, symbol: str, max_slippage_pips: float) -> int:
        """
        Convert 'pips' into MT5 'points' deviation.
        For most FX pairs: 1 pip = 10 points when digits=5 or 3.
        For digits=4 or 2: 1 pip = 1 point.
        """
        info = mt5.symbol_info(symbol)
        if not info:
            return 20  # fallback

        digits = info.digits or 5
        # pip->point factor
        pip_factor = 10 if digits in (3, 5) else 1
        return int(max_slippage_pips * pip_factor)

    def resolve_symbol(self, symbol: str) -> str:
        base = (symbol or "").upper().strip()

        # If exact exists, use it
        info = mt5.symbol_info(base)
        if info:
            return base

        # Try alias list
        for cand in self.SYMBOL_ALIASES.get(base, []):
            info = mt5.symbol_info(cand)
            if info:
                return cand

        # Last resort: scan all symbols for prefix match
        all_syms = mt5.symbols_get()
        if all_syms:
            for s in all_syms:
                name = getattr(s, "name", "")
                if name.upper() == base:
                    return name
            for s in all_syms:
                name = getattr(s, "name", "")
                if name.upper().startswith(base):
                    return name

        return base  # fallback (will fail gracefully later)

    def get_account_info(self):
        import MetaTrader5 as mt5

        acc = mt5.account_info()
        if acc is None:
            return None

        return {
            "balance": float(acc.balance),
            "equity": float(acc.equity),
        }

        self._log(trade, TradeAuditEvent.EventType.MT5_CONNECT_START, {}, ctx)

    def _ensure_connected(self, max_wait_sec: int = 10) -> None:
        """
        Ensures MT5 is initialized and usable inside THIS Django process.
        Raises RuntimeError with a useful message if it cannot connect.
        """
        # Already initialized in this process?
        ti = mt5.terminal_info()
        ai = mt5.account_info()
        if ti is not None and ai is not None:
            return

        # Try initialize (attach to running terminal first)
        if not mt5.initialize():
            # Try with explicit path
            if not mt5.initialize(path=self.DEFAULT_MT5_PATH):
                code, msg = mt5.last_error()
                raise RuntimeError(f"MT5 initialize failed: ({code}) {msg}")

        # Wait until terminal/account becomes available (MT5 can be slow on startup)
        start = time.time()
        while time.time() - start < max_wait_sec:
            if mt5.terminal_info() is not None and mt5.account_info() is not None:
                return
            time.sleep(0.25)


        # If still not ready:
        code, msg = mt5.last_error()
        raise RuntimeError(f"MT5 not ready after init: ({code}) {msg}")

       #self._log(trade, TradeAuditEvent.EventType.MT5_CONNECT_OK, {}, ctx)

    def ensure_connected(self) -> None:
        if mt5.initialize():
            return
        raise RuntimeError(f"MT5 initialize failed: {mt5.last_error()}")

    def copy_rates(self, symbol: str, timeframe: int, bars: int):
        """
        Returns list-like rates from MT5 or [] if none.
        timeframe must be an MT5 TIMEFRAME_* constant.
        """
        self.ensure_connected()

        symbol = symbol.strip().upper()

        # Ensure symbol is available in Market Watch
        if not mt5.symbol_select(symbol, True):
            raise RuntimeError(f"symbol_select failed for {symbol}: {mt5.last_error()}")

        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, int(bars))

        if rates:
            last = rates[-1]
            candle = {
                "time": int(last["time"]),
                "open": float(last["open"]),
                "high": float(last["high"]),
                "low": float(last["low"]),
                "close": float(last["close"]),
                "volume": float(last.get("tick_volume", 0)),
            }

            broadcast_candle(symbol, timeframe, candle)

        if rates is None:
            # failure case
            print("copy_rates_from_pos returned None:", mt5.last_error())
            return []

        # can be empty array too
        return rates

    def _resolve_filling_mode(self, symbol: str) -> int:
        info = mt5.symbol_info(symbol)
        if not info:
            return mt5.ORDER_FILLING_RETURN  # safest fallback

        fm = info.filling_mode

        # Prefer IOC → FOK → RETURN
        candidates = [
            mt5.ORDER_FILLING_IOC,
            mt5.ORDER_FILLING_FOK,
            mt5.ORDER_FILLING_RETURN,
        ]

        for c in candidates:
            if fm == c:
                return c

        return mt5.ORDER_FILLING_RETURN

    def _log(self, trade, event_type, payload=None, ctx=None):
        try:
            audit_event(trade, event_type, payload or {}, ctx)
        except Exception:
            # never break trading if audit logging fails
            pass

    TIMEFRAME_MAP = {
        "M1": mt5.TIMEFRAME_M1,
        "M2": mt5.TIMEFRAME_M2,
        "M3": mt5.TIMEFRAME_M3,
        "M5": mt5.TIMEFRAME_M5,
        "M10": mt5.TIMEFRAME_M10,
        "M15": mt5.TIMEFRAME_M15,
        "M30": mt5.TIMEFRAME_M30,
        "H1": mt5.TIMEFRAME_H1,
        "H2": mt5.TIMEFRAME_H2,
        "H4": mt5.TIMEFRAME_H4,
        "H6": mt5.TIMEFRAME_H6,
        "H8": mt5.TIMEFRAME_H8,
        "H12": mt5.TIMEFRAME_H12,
        "D1": mt5.TIMEFRAME_D1,
        "W1": mt5.TIMEFRAME_W1,
        "MN1": mt5.TIMEFRAME_MN1,
    }

    # TICK = symbol only
    def get_symbol_tick(self, symbol: str):
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            return None
        return {
            "time": int(tick.time),
            "bid": float(tick.bid),
            "ask": float(tick.ask),
            "last": float(tick.last),
        }

    #  RATES/CANDLES = symbol + timeframe + bars
    def get_symbol_rates(self, symbol: str, timeframe: str, bars: int = 300):
        self.ensure_connected()

        symbol = (symbol or "").strip().upper()
        timeframe = (timeframe or "").strip().upper()
        tf = TIMEFRAMES.get(timeframe)

        if tf is None:
            raise ValueError(f"Unsupported timeframe: {timeframe}")

        # Make sure symbol is available in Market Watch
        info = mt5.symbol_info(symbol)
        if info is None:
            raise ValueError(f"Symbol not found in MT5: {symbol}")

        if not info.visible:
            if not mt5.symbol_select(symbol, True):
                raise RuntimeError(f"symbol_select failed for {symbol}: {mt5.last_error()}")

        rates = mt5.copy_rates_from_pos(symbol, tf, 0, int(bars))

        # Debug info (this is the key)
        err = mt5.last_error()
        print(f"[MT5] copy_rates_from_pos symbol={symbol} tf={timeframe} bars={bars} "
              f"rates_len={(0 if rates is None else len(rates))} last_error={err}", flush=True)

        return rates
    # ==========================
    # Alex / Zone Engine Candles
    # ==========================
    def get_candles(self, symbol: str, timeframe: str, bars: int):
        """
        Alex-friendly candles:
        - ensures MT5 connected
        - resolves broker symbol (suffixes like .i / m)
        - returns list[dict] with time/open/high/low/close
        - returns [] when market is closed / no data
        """
        self._ensure_connected()

        resolved = self.resolve_symbol(symbol)
        if not resolved:
            return []

        # Ensure symbol is selectable/visible
        try:
            self.ensure_symbol(resolved)
        except Exception:
            return []

        # Use your existing wrapper (count -> bars)
        return self.get_rates(symbol=resolved, timeframe=timeframe, count=int(bars))



def get_market_tick(symbol: str) -> dict:
    if not mt5.initialize():
        return {"error": "MT5 initialize failed", "status": 500, "last_error": mt5.last_error()}

    info = mt5.symbol_info(symbol)
    if info is None:
        #mt5.shutdown()
        return {"error": f"Symbol {symbol} not found", "status": 404}

    # Ensure symbol is visible in Market Watch
    if not info.visible:
        mt5.symbol_select(symbol, True)

    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        #mt5.shutdown()
        return {"error": f"No tick data for {symbol}. Make sure MT5 is open and the market is active.", "status": 404}

    bid = float(tick.bid) if tick.bid is not None else None
    ask = float(tick.ask) if tick.ask is not None else None

    data = {
        "symbol": symbol,
        "bid": bid,
        "ask": ask,
        "spread": (ask - bid) if (bid is not None and ask is not None) else None,
        "time_msc": int(tick.time_msc) if tick.time_msc is not None else None,
       }

    #mt5.shutdown()
    return data


class TradingService:
    def create_trade(self, symbol: str, side: str, lot: float, ctx: AuditCtx | None = None) -> Trade:
        trade = Trade.objects.create(symbol=symbol, side=side, lot=lot, status="CREATED")
        audit_event(trade, TradeAuditEvent.EventType.TRADE_CREATED, {
            "symbol": symbol, "side": side, "lot": float(lot),
        }, ctx)
        return trade






class MT5ConnectView(APIView):
    """
    Secure MT5 connect endpoint.
    Requires:
    - JWT authentication
    - Re-auth token (password + OTP)
    """
    permission_classes = [IsAuthenticated, RequiresReauth]

    def post(self, request):
        mt5_service = MT5Service()

        try:
            mt5_service.connect()
        except Exception as e:
            return Response(
                {"detail": f"MT5 connection failed: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"detail": "MT5 connected successfully."},
            status=status.HTTP_200_OK,
        )
