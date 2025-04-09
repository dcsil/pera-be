from rest_framework import serializers
from texts.models import Passage, Sentence


class ParseTextRequestSerializer(serializers.Serializer):
    text = serializers.CharField()
    title = serializers.CharField(required=False, allow_blank=True)
    language = serializers.CharField(required=False, allow_blank=True)


class ParseTextResponseSerializer(serializers.Serializer):
    passage_id = serializers.IntegerField()
    sentences = serializers.ListField(child=serializers.CharField())


class ErrorResponseSerializer(serializers.Serializer):
    error = serializers.CharField()


class SentenceSerializer(serializers.ModelSerializer):
    passage_id = serializers.IntegerField(source="passage.passage_id", read_only=True)

    class Meta:
        model = Sentence
        fields = (
            "sentence_id",
            "passage_id",
            "text",
            "completion_status",
            "created_at",
        )


class PassageSerializer(serializers.ModelSerializer):
    sentences = SentenceSerializer(many=True, read_only=True, source="sentence_set")

    class Meta:
        model = Passage
        fields = (
            "passage_id",
            "title",
            "language",
            "difficulty",
            "created_at",
            "sentences",
        )
