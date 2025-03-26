from rest_framework import serializers

class PronunciationCheckSerializer(serializers.Serializer):
    audio = serializers.FileField()
    text = serializers.CharField()

class PronunciationAssessmentResponseSerializer(serializers.Serializer):
    AccuracyScore = serializers.FloatField()
    FluencyScore = serializers.FloatField()
    PronunciationScore = serializers.FloatField()
    JsonResult = serializers.JSONField()

class ErrorResponseSerializer(serializers.Serializer):
    error = serializers.CharField()
