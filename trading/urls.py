from django.urls import path
from .views.market import LiveMarketDataView
from trading.views.live import trade_history

from .views.market import mt5_market_view
from .views.live import market_live  # keep whatever you already have
from .views.live import execute_trade, trade_list
from trading.views.live import close_trade, modify_trade, emergency_close_all

from trading.views.live import  live_orders, live_positions
from trading.views.history import TradeHistoryListView, TradeDetailView
from trading.views.live import AuditExportView
from trading.views.audit_export import audit_export, AuditVerifyView
from .mt5.service import MT5ConnectView

urlpatterns = [
    path("market/live/", LiveMarketDataView.as_view(), name="market_live"),
    # keep your existing route(s)
    path("market/live/", market_live, name="market_live"),

    # add this new MT5 market endpoint
    path("mt5/market/", mt5_market_view, name="mt5_market"),

    path("live/execute/", execute_trade, name="trade-execute"),
    path("live/trades/", trade_list, name="trade-list"),

    path("live/close/", close_trade, name="close-trade"),
    path("live/modify/", modify_trade),
    path("live/emergency-close-all/", emergency_close_all),

    path("live/positions/", live_positions, name="live-positions"),
    path("live/orders/", live_orders, name="live-orders"),

    path("history/", trade_history, name="trade-history"),

    path("live/history/", TradeHistoryListView.as_view(), name="trade-history"),
    path("live/trades/<int:pk>/", TradeDetailView.as_view(), name="trade-detail"),

    path("audit/export/", audit_export, name="audit-export"),

    path("audit/export", audit_export, name="audit-export"),
    path("audit/verify", AuditVerifyView.as_view(), name="audit-verify"),
    #path("audit/trades/<int:trade_id>/export", TradeAuditExportView.as_view(), name="trade-audit-export"),
    path("connect/", MT5ConnectView.as_view(), name="mt5-connect"),
]



