import json
from urllib.parse import parse_qs
from channels.generic.websocket import AsyncWebsocketConsumer
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth.models import AnonymousUser

class MarketConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        qs = parse_qs(self.scope["query_string"].decode())
        self.symbol = (qs.get("symbol") or ["XAUUSD"])[0]
        self.timeframe = (qs.get("timeframe") or ["M15"])[0]
        token = (qs.get("token") or [""])[0]

        user = await self._auth_user(token)
        if not user or user.is_anonymous:
            await self.close(code=4401)  # unauthorized
            return

        self.group_name = f"market_{self.symbol}_{self.timeframe}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def market_candle(self, event):
        # event["data"] is dict for candle update
        await self.send(text_data=json.dumps(event["data"]))

    async def _auth_user(self, raw_token: str):
        try:
            jwt_auth = JWTAuthentication()
            validated = jwt_auth.get_validated_token(raw_token)
            return jwt_auth.get_user(validated)
        except Exception:
            return AnonymousUser()
