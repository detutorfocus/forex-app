from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import PushSubscription


class PushSubscribeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        sub = request.data.get("subscription") or {}
        endpoint = sub.get("endpoint")
        keys = sub.get("keys") or {}
        p256dh = keys.get("p256dh")
        auth = keys.get("auth")

        if not (endpoint and p256dh and auth):
            return Response({"ok": False, "error": "invalid_subscription"}, status=400)

        PushSubscription.objects.update_or_create(
            endpoint=endpoint,
            defaults={
                "user": request.user,
                "p256dh": p256dh,
                "auth": auth,
                "user_agent": request.META.get("HTTP_USER_AGENT", "")[:255],
            },
        )
        return Response({"ok": True})
