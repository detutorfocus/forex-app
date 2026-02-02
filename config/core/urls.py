"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from .views import home
from django.contrib import admin
from django.urls import path, include
from notifications.views import PushSubscribeView
from accounts.views import TelegramLoginView

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", home, name="home"),
    # Auth (JWT)
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # Apps
    path("api/auth/accounts/", include("accounts.urls")),
    path("api/auth/", include("accounts.urls")),
    path("api/trading/", include("trading.urls")),

    path("trading/", include("trading.urls")),
    path("api/dashboard", include("config.trade_dashboard.urls")),

    path("", include("trading.urls")),

    path("ai_assistant/", include("ai_assistant.urls")),
    path("ai/", include("ai_assistant.urls")),

    path("ai/notify/subscribe/", PushSubscribeView.as_view()),

    path("ai/notify/", include("notifications.urls")),

    path("api/security/", include("security.urls")),

    path("api/auth/", include("security.jwt_urls")),
    path("api/auth/", include("security.reauth_urls")),
    path("api/auth/", include("security.password_reset_urls")),

    path("api/mt5/", include("trading.urls")),

    path("api/accounts/", include("accounts.urls")),

    path("api/auth/", include("dj_rest_auth.urls")),
    path("api/auth/registration/", include("dj_rest_auth.registration.urls")),
    path("api/auth/social/", include("dj_rest_auth.registration.urls")),
    path("auth/telegram/login/", TelegramLoginView.as_view(), name="telegram-login"),


]

