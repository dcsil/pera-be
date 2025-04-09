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
from speech_processing.models import Feedback
from accounts.decorators import require_authentication
from accounts.models import Event
from texts.models import Sentence

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

# @require_authentication
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
            sentence_id = request.data.get('sentence_id', None)

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

                feedback = Feedback.objects.create(
                    azure_id=result.result_id,
                    user=request.user.userprofile,
                    sentence=sentence_id if sentence_id else None,
                    display_text=reference_text,
                    accuracy_score=assessment_result.accuracy_score,
                    fluency_score=assessment_result.fluency_score,
                    completeness_score=assessment_result.completeness_score,
                    pron_score=assessment_result.pronunciation_score,
                    json_data=result.properties.get(
                        speechsdk.PropertyId.SpeechServiceResponse_JsonResult
                    ),
                )

                # Record an event that the user completed a practice
                Event.objects.create(
                    user=request.user.userprofile,
                    event_type="PRACTICE_PRON",
                )

                # Mark the sentence as complete
                if sentence_id:
                    try:
                        sentence = Sentence.objects.get(sentence_id=sentence_id)
                        sentence.completion_status = True
                        sentence.save()
                    except Sentence.DoesNotExist:
                        return Response({"error": "Sentence not found."}, status=404)

                response_data = {
                    "AccuracyScore": feedback.accuracy_score,
                    "FluencyScore": feedback.fluency_score,
                    "PronunciationScore": feedback.pron_score,
                    "JsonResult": feedback.json_data,
                }
                return Response(response_data, status=200)
            else:
                return Response({"error": "Speech not recognized or an error occurred."}, status=400)

        except Exception as e:
            return Response({"error": str(e)}, status=500)
