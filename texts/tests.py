from django.urls import reverse
from rest_framework.test import APITestCase
from texts.models import Passage, Sentence
from unittest.mock import patch

class ParseTextViewTests(APITestCase):
    def setUp(self):
        self.url = reverse('parse-text')

    def test_valid_input_creates_passage_and_sentences(self):
        data = {
            "text": "This is the first sentence. This is the second sentence.",
            "title": "Test Passage",
            "language": "en"
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertIn("passage_id", response.data)
        self.assertIn("sentences", response.data)
        self.assertEqual(len(response.data["sentences"]), 2)

        passage = Passage.objects.get(passage_id=response.data["passage_id"])
        self.assertEqual(passage.title, "Test Passage")
        self.assertEqual(passage.language, "en")
        self.assertEqual(passage.difficulty, "Custom")

        sentences = Sentence.objects.filter(passage=passage)
        self.assertEqual(sentences.count(), 2)
        self.assertEqual(sentences.first().text, "This is the first sentence.")
        self.assertEqual(sentences.last().text, "This is the second sentence.")

    def test_invalid_input_missing_required_fields(self):
        data = {
            "text": "Some text"
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.data)

    def test_no_text_provided(self):
        data = {
            "text": "    ",
            "title": "Empty Text Passage",
            "language": "en"
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.data)
        self.assertEqual(response.data["error"], "Invalid input data.")

    def test_tokenization_error(self):
        data = {
            "text": "This should cause error",
            "title": "Error Passage",
            "language": "en"
        }
        with patch("texts.views.PunktSentenceTokenizer.tokenize", side_effect=Exception("Test tokenization error")):
            response = self.client.post(self.url, data, format="json")
            self.assertEqual(response.status_code, 500)
            self.assertIn("error", response.data)
            self.assertIn("Test tokenization error", response.data["error"])
