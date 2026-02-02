from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

channel_layer = get_channel_layer()

def broadcast_candle(symbol: str, timeframe: str, candle_dict: dict):
    """
    Broadcast a candle update to all connected WebSocket clients
    subscribed to this symbol + timeframe.
    """
    group = f"market_{symbol}_{timeframe}"

    async_to_sync(channel_layer.group_send)(
        group,
        {
            "type": "market.candle",
            "data": {
                "type": "candle",
                **candle_dict,
            },
        },
    )
