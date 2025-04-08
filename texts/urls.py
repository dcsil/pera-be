from django.urls import path
from .views import ParseTextView, GetUserPassagesView, GetPassageSentencesView

urlpatterns = [
    path("parse-text/", ParseTextView.as_view(), name="parse-text"),
    path('user-passages/', GetUserPassagesView.as_view(), name='get_user_passages'),
    path('passage-sentences/<int:passage_id>/', GetPassageSentencesView.as_view(), name='get_passage_sentences'),
]