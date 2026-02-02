from rest_framework import serializers

class MT5ConnectSerializer(serializers.Serializer):
    login = serializers.IntegerField()
    server = serializers.CharField(max_length=120)
    password = serializers.CharField(max_length=255)
