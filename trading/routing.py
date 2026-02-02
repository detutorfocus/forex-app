# market/routing.py
from django.urls import re_path
from .consumers import MarketConsumer

websocket_urlpatterns = [
    re_path(r"^ws/market/(?P<symbol>[^/]+)/(?P<tf>[^/]+)/$", MarketConsumer.as_asgi()),
]
