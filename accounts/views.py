from django.shortcuts import render
from django.contrib.auth.models import  User
from rest_framework.decorators import api_view
from django.contrib.auth import authenticate
# Create your views here.
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated

from security.permissions import RequiresReauth
from .models import MT5Account
from .serializers import MT5ConnectSerializer
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from trading.mt5.bridge_client import bridge_post
from .telegram_auth import verify_telegram_auth

@api_view(['POST'])
def register(request):
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')
    password2 = request.data.get('password2')

    if not username or not password:
        return Response(
            {'error': 'Username and password are required'},
status= status.HTTP_400_BAD_REQUEST
        )
    if password2 is not None and password != password2:
        return Response({"error": "passwords do not match"}, 
           status=status.HTTP_400_BAD_REQUEST
             )
    if User.objects.filter(username=username).exists():
        return Response(
            {'error': 'Username already exists'},
status=status.HTTP_400_BAD_REQUEST
        )
    user =User.objects.create_user(
        username = username,
        password= password,
        email= email
    )
    return Response(
        {'message': 'User registered successfully'},
        status= status.HTTP_201_CREATED
    )
@api_view(['POST'])
def login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')

    user = authenticate(username=username, password=password)

    if user is None:
        return Response(
            {'error': 'Invalid credentials'},
status=status.HTTP_401_UNAUTHORIZED
        )
    return Response(
        {'message': 'Login successful'},
        status=status.HTTP_200_OK
    )

# import your MT5Service from wherever it lives now
from trading.mt5.service import MT5Service # adjust path to your file


class MT5ConnectView(APIView):
    permission_classes = [IsAuthenticated, RequiresReauth]

    def post(self, request):
        s = MT5ConnectSerializer(data=request.data)
        s.is_valid(raise_exception=True)

        login = s.validated_data["login"]
        server = s.validated_data["server"].strip()
        password = s.validated_data["password"]


        # inside MT5ConnectView.post
        result = bridge_post("/connect", {
            "user_id": request.user.id,
            "login": login,
            "server": server,
            "password": password,
        })

        mt5_account, _ = MT5Account.objects.get_or_create(user=request.user)
        mt5_account.login = login
        mt5_account.server = server
        mt5_account.set_password(password)
        mt5_account.is_active = True
        mt5_account.last_connected_at = timezone.now()
        mt5_account.save()

        # Optional: verify credentials by attempting a session/login with your service
        # (Implementation depends on how your MT5Service works)
        try:
            mt5 = MT5Service(login=login, server=server, password=password)  # adjust constructor
            mt5.connect()
            # If you have a login/auth method, call it here.
        except TypeError:
            # If your MT5Service does not accept args, skip verification for now
            pass
        except Exception as e:
            return Response(
                {"detail": f"MT5 connection failed: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        obj, _ = MT5Account.objects.update_or_create(
            user=request.user,
            defaults={
                "login": login,
                "server": server,
                "password": password,
                "is_active": True,
                "last_connected_at": timezone.now(),
            },
        )


        return Response(
            {
                "detail": "MT5 account saved successfully.",
                "server": obj.server,
                "login": obj.login,
            },
            status=status.HTTP_200_OK,
        )

from .models import MT5Account, BrokerPortal

class WithdrawalDestinationView(APIView):
    permission_classes = [IsAuthenticated]  # or add RequiresReauth if you want

    def get(self, request):
        mt5 = MT5Account.objects.filter(user=request.user, is_active=True).first()
        if not mt5:
            return Response(
                {"detail": "No MT5 account connected yet."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        server = (mt5.server or "").strip()
        s_lower = server.lower()

        matched = None
        for p in BrokerPortal.objects.filter(is_active=True):
            if any(str(k).lower() in s_lower for k in (p.server_keywords or [])):
                matched = p
                break

        if matched:
            url = matched.withdraw_url or matched.portal_url
            return Response(
                {
                    "broker_known": True,
                    "broker_name": matched.name,
                    "server": server,
                    "withdraw_url": url,
                    "note": "Withdrawals are handled by your broker portal.",
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {
                "broker_known": False,
                "server": server,
                "withdraw_url": "",
                "note": "Withdrawals are handled by your broker’s portal. Open your broker portal (where you deposited) and withdraw from there.",
            },
            status=status.HTTP_200_OK,
        )



User = get_user_model()


class TelegramLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # Telegram sends data like: id, first_name, username, photo_url, auth_date, hash...
        data = request.data.copy()

        ok, err = verify_telegram_auth(data)
        if not ok:
            return Response({"detail": err}, status=status.HTTP_400_BAD_REQUEST)

        tg_id = str(data.get("id"))
        username = (data.get("username") or "").strip()
        first_name = (data.get("first_name") or "").strip()
        last_name = (data.get("last_name") or "").strip()

        # Decide how you want to map Telegram users to Django users.
        # Common: create a user with a synthetic email or store tg_id in a profile.
        email = f"{tg_id}@telegram.local"

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "first_name": first_name,
                "last_name": last_name,
            },
        )

        # If you use SimpleJWT:
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "detail": "Logged in with Telegram.",
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "username": username,
            },
            status=status.HTTP_200_OK,
        )


