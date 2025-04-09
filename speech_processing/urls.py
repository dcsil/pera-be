from django.urls import path
from .views import PronunciationAssessmentView

urlpatterns = [
    path(
        "scripted-assessment/",
        PronunciationAssessmentView.as_view(),
        name="scripted-assessment",
    ),
]
