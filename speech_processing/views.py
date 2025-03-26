import azure.cognitiveservices.speech as speechsdk
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
import tempfile
import traceback
import os
from .serializers import (
    PronunciationAssessmentResponseSerializer,
    ErrorResponseSerializer,
)
from drf_spectacular.utils import extend_schema
from decouple import config

SPEECH_KEY = config("SPEECH_KEY")
SPEECH_REGION = config("SPEECH_REGION")


class RequestFileReaderCallback(speechsdk.audio.PullAudioInputStreamCallback):
    def __init__(self, request_file, chunk_size=65536):
        super().__init__()
        self._chunks = request_file.chunks(chunk_size=chunk_size)
        self._latest = []
        self._latest_ind = 0

    def read(self, buffer):
        if self._latest_ind >= len(self._latest):
            try:
                self._latest = self._chunks.__next__()
                self._latest_ind = 0
            except StopIteration:
                return 0
            if len(self._latest) == 0:
                return 0
        sz = min(len(self._latest) - self._latest_ind, buffer.nbytes)
        buffer[:sz] = self._latest[self._latest_ind : self._latest_ind + sz]
        self._latest_ind += sz
        return sz


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

            callback = RequestFileReaderCallback(audio_file)
            stream = speechsdk.audio.PullAudioInputStream(
                stream_format=speechsdk.audio.AudioStreamFormat(
                    compressed_stream_format=speechsdk.AudioStreamContainerFormat.ANY
                ),
                pull_stream_callback=RequestFileReaderCallback(audio_file),
            )

            speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
            audio_config = speechsdk.audio.AudioConfig(stream=stream)

            pronunciation_config = speechsdk.PronunciationAssessmentConfig(
                reference_text=reference_text,
                granularity=speechsdk.PronunciationAssessmentGranularity.Phoneme,
            )
            pronunciation_config.enable_prosody_assessment()

            recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
            pronunciation_config.apply_to(recognizer)

            # TODO: Change this to continuous recognition
            result = recognizer.recognize_once()

            # Cleanup
            del recognizer

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
