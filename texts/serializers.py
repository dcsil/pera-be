from rest_framework import serializers

class ParseTextRequestSerializer(serializers.Serializer):
    text = serializers.CharField()
    title = serializers.CharField(required=True)
    language = serializers.CharField(required=True)

class ParseTextResponseSerializer(serializers.Serializer):
    passage_id = serializers.IntegerField()
    sentences = serializers.ListField(child=serializers.CharField())

class ErrorResponseSerializer(serializers.Serializer):
    error = serializers.CharField()
