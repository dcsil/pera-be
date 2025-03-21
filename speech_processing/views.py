import azure.cognitiveservices.speech as speechsdk
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
import tempfile
import os
from .serializers import (
    PronunciationAssessmentResponseSerializer,
    ErrorResponseSerializer,
)
from drf_spectacular.utils import extend_schema
from decouple import config

SPEECH_KEY = config("SPEECH_KEY")
SPEECH_REGION = config("SPEECH_REGION")

class PronunciationAssessmentView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    @extend_schema(
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'audio': {'type': 'string', 'format': 'binary'},
                    'text': {'type': 'string'},
                },
                'required': ['audio', 'text']
            }
        },
        responses={
            200: PronunciationAssessmentResponseSerializer,
            400: ErrorResponseSerializer,
            500: ErrorResponseSerializer,
        },
    )
    def post(self, request, *args, **kwargs):
        try:
            audio_file = request.FILES.get('audio')
            reference_text = request.data.get('text', '')

            if not audio_file or not reference_text:
                return Response({"error": "Audio file and reference text required."}, status=400)

            # Temporary audio save
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio_file:
                for chunk in audio_file.chunks():
                    temp_audio_file.write(chunk)
                temp_audio_path = temp_audio_file.name

            speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
            audio_config = speechsdk.audio.AudioConfig(filename=temp_audio_path)

            pronunciation_config = speechsdk.PronunciationAssessmentConfig(
                reference_text=reference_text,
                granularity=speechsdk.PronunciationAssessmentGranularity.Phoneme,
            )
            pronunciation_config.enable_prosody_assessment()

            recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
            pronunciation_config.apply_to(recognizer)
            result = recognizer.recognize_once()

            # Cleanup
            del recognizer
            os.remove(temp_audio_path)

            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                assessment_result = speechsdk.PronunciationAssessmentResult(result)
                response_data = {
                    "AccuracyScore": assessment_result.accuracy_score,
                    "FluencyScore": assessment_result.fluency_score,
                    "PronunciationScore": assessment_result.pronunciation_score,
                    "JsonResult": result.properties.get(speechsdk.PropertyId.SpeechServiceResponse_JsonResult),
                }
                return Response(response_data, status=200)
            else:
                return Response({"error": "Speech not recognized or an error occurred."}, status=400)

        except Exception as e:
            return Response({"error": str(e)}, status=500)
