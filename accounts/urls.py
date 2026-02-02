from django.urls import path
from .views import register, login_view

from .views import MT5ConnectView, WithdrawalDestinationView
from .social_auth_views import GoogleLogin, FacebookLogin, XLogin
from .views import TelegramLoginView  # you already created this


urlpatterns = [
    path('register/', register),
    path('login/', login_view),

    path("mt5/connect/", MT5ConnectView.as_view(), name="mt5-connect"),
    path("withdraw/destination/", WithdrawalDestinationView.as_view(), name="withdraw-destination"),

    # Telegram (custom)
    path("auth/telegram/login/", TelegramLoginView.as_view(), name="telegram-login"),

    # Social OAuth (returns JWT immediately)
    path("auth/google/", GoogleLogin.as_view(), name="google-login"),
    path("auth/facebook/", FacebookLogin.as_view(), name="facebook-login"),
    path("auth/x/", XLogin.as_view(), name="x-login"),
]