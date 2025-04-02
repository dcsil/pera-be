from rest_framework import serializers


class SignUpRequestSerializer(serializers.Serializer):
    email = serializers.CharField(max_length=255)
    name = serializers.CharField(max_length=255)
    password = serializers.CharField()
    base_language = serializers.CharField(max_length=50)
