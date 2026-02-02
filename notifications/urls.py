from django.urls import path
from .views import PushSubscribeView

urlpatterns = [
    path("subscribe/", PushSubscribeView.as_view(), name="push-subscribe"),

]
