from drf_spectacular.types import OpenApiTypes
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema
from nltk.tokenize.punkt import PunktSentenceTokenizer

from .serializers import (
    ParseTextRequestSerializer,
    ParseTextResponseSerializer,
    ErrorResponseSerializer,
    PassageSerializer,
    SentenceSerializer,
    GenerateTextRequestSerializer,
)
from texts.models import Passage, Sentence
from accounts.decorators import require_authentication
from .services import cohere
from .services.cohere import CohereGenerationError


@require_authentication()
class ParseTextView(APIView):
    @extend_schema(
        request=ParseTextRequestSerializer,
        responses={
            200: ParseTextResponseSerializer,
            400: ErrorResponseSerializer,
        },
    )
    def post(self, request):
        serializer = ParseTextRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": "Invalid input data."}, status=status.HTTP_400_BAD_REQUEST
            )

        text = serializer.validated_data["text"].strip()
        title = serializer.validated_data.get("title", "Untitled Passage")
        language = serializer.validated_data.get("language", "en")

        if not text:
            return Response(
                {"error": "No text provided."}, status=status.HTTP_400_BAD_REQUEST
            )

        tokenizer = PunktSentenceTokenizer()
        try:
            sentences = tokenizer.tokenize(text)
        except Exception as e:
            return Response(
                {"error": f"Error processing text: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if not sentences:
            return Response(
                {"error": "No sentences found."}, status=status.HTTP_400_BAD_REQUEST
            )

        user_profile = getattr(request.user, "userprofile", None)
        if not user_profile:
            return Response(
                {"error": "UserProfile not found."}, status=status.HTTP_400_BAD_REQUEST
            )

        passage = Passage.objects.create(
            user=user_profile,
            language=language,
            title=title,
            difficulty="Custom",
        )

        for sentence_text in sentences:
            Sentence.objects.create(
                passage=passage, text=sentence_text, completion_status=False
            )

        return Response(
            {"passage_id": passage.passage_id, "sentences": sentences},
            status=status.HTTP_200_OK,
        )


@require_authentication()
class GetUserPassagesView(APIView):
    @extend_schema(responses=PassageSerializer(many=True))
    def get(self, request):
        user_profile = getattr(request.user, "userprofile", None)
        if not user_profile:
            return Response(
                {"error": "UserProfile not found."}, status=status.HTTP_400_BAD_REQUEST
            )

        passages = Passage.objects.filter(user=user_profile)
        serializer = PassageSerializer(passages, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@require_authentication()
class GetPassageSentencesView(APIView):
    @extend_schema(responses=SentenceSerializer(many=True))
    def get(self, request, passage_id):
        try:
            passage = Passage.objects.get(
                passage_id=passage_id, user=request.user.userprofile
            )
            sentences = Sentence.objects.filter(passage=passage)
            serializer = SentenceSerializer(sentences, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Passage.DoesNotExist:
            return Response(
                {"error": "Passage not found."},
                status=status.HTTP_404_NOT_FOUND,
            )


@require_authentication
class GeneratePassageView(APIView):
    @extend_schema(
        request=GenerateTextRequestSerializer,
        responses={
            200: OpenApiTypes.STR,
            400: ErrorResponseSerializer,
        },
    )
    def post(self, request):
        serializer = GenerateTextRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": "Invalid passage generation request."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        passage_description = serializer.validated_data["description"]
        difficulty = serializer.validated_data["difficulty"]

        # TODO: sanitize user passage description

        try:
            passage = cohere.generate_passage(passage_description, difficulty)
        except CohereGenerationError:
            return Response(
                {"error": "Passage generation failed."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(passage, status=status.HTTP_200_OK)
