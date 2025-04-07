from django.urls import path
from .views import ParseTextView

urlpatterns = [
    path("parse-text/", ParseTextView.as_view(), name="parse-text"),
]