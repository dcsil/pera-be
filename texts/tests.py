from django.urls import reverse
from rest_framework.test import APITestCase
from texts.models import Passage, Sentence
from unittest.mock import patch
from django.contrib.auth import get_user_model
from accounts.models import UserProfile

class ParseTextViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="authed@example.com", password="testpass")
        self.user_profile = UserProfile.objects.create(
            auth_user=self.user,
            default_settings={"theme": "light", "notifications": True},
            base_language="en"
        )
        # Force authenticate so we don’t get 401 from @require_authentication
        self.client.force_authenticate(user=self.user)
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
            "title": "Test Passage",
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

User = get_user_model()

class GetUserPassagesViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="testemail@example.com", password="testpass", name="testuser")
        self.user_profile = UserProfile.objects.create(
            auth_user=self.user,
            default_settings={"theme": "light", "notifications": True},
            base_language="en"
        )

        self.url = reverse("get_user_passages")
        self.passage1 = Passage.objects.create(
            user=self.user_profile,
            title="Passage 1",
            language="en",
            difficulty="Custom"
        )
        self.passage2 = Passage.objects.create(
            user=self.user_profile,
            title="Passage 2",
            language="en",
            difficulty="Custom"
        )
        # Create a passage for another user.
        self.passage_other = Passage.objects.create(
            title="Other Passage",
            language="en",
            difficulty="Custom"
        )

    def test_get_user_passages_authenticated(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        titles = [p["title"] for p in response.data]
        self.assertIn("Passage 1", titles)
        self.assertIn("Passage 2", titles)

    def test_get_user_passages_unauthenticated(self):
        # Now that the view requires authentication, expect 401 instead of an empty list.
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)


class GetPassageSentencesViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="testemail@example.com", password="testpass", name="testuser")
        self.user_profile = UserProfile.objects.create(
            auth_user=self.user,
            default_settings={"theme": "light", "notifications": True},
            base_language="en"
        )
        self.passage = Passage.objects.create(
            user=self.user_profile,
            title="Test Passage",
            language="en",
            difficulty="Custom"
        )
        self.sentence1 = Sentence.objects.create(
            passage=self.passage,
            text="Sentence one.",
            completion_status=False
        )
        self.sentence2 = Sentence.objects.create(
            passage=self.passage,
            text="Sentence two.",
            completion_status=False
        )
        self.url = reverse("get_passage_sentences", kwargs={"passage_id": self.passage.passage_id})

        # Force authenticate for these tests too.
        self.client.force_authenticate(user=self.user)

    def test_get_passage_sentences_valid(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        texts = [s["text"] for s in response.data]
        self.assertIn("Sentence one.", texts)
        self.assertIn("Sentence two.", texts)

    def test_get_passage_sentences_not_found(self):
        # We remain authenticated, but use a non-existent passage_id
        url = reverse("get_passage_sentences", kwargs={"passage_id": 99999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
        self.assertIn("error", response.data)
        self.assertEqual(response.data["error"], "Passage not found.")
