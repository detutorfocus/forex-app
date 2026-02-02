from django.urls import path, include
from core.views import home
from core.views import dashboard

urlpatterns = [
    path("", home),
    path('dashboard/', dashboard, name='dashboard'),
    path("api/", include("core.urls")),
]