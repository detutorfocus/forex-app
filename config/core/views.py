from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.http import JsonResponse
from rest_framework.permissions import IsAuthenticated



# Create your views here.


def home(request):
    return JsonResponse({
        "status": "success",
        "service": "Forex Backend",
        "message": "Service is running",
        "endpoint": {
            "token": "/api/token",
            "refresh": "/api/token/refresh/",
            "accounts": "/api/accounts/",
            "trading": "/api/trading/"
        }
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard(request):
    return Response({
        "message": "Welcome to your forex dashboard",
        "user": request.user.username,
        "is_authenticated": request.user.is_authenticated
    })


