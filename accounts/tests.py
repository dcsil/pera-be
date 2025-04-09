from django.urls import reverse
from rest_framework.test import APITestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from accounts.models import UserProfile, Event
from speech_processing.models import Feedback
from datetime import timedelta
import pdb

User = get_user_model()

class DashboardViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="authed@example.com", password="testpass")
        self.user_profile = UserProfile.objects.create(
            auth_user=self.user,
            default_settings={"theme": "light", "notifications": True},
            base_language="en"
        )
        self.url = reverse("dashboard")

    def test_dashboard_no_data(self):
        """
        If there is no data for the user, ensure the endpoint returns defaults (zero-like values).
        """
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.data.get("progress_dashboard", {})
        stats = data.get("stats", {})
        self.assertEqual(stats.get("overall"), 0.0)
        self.assertEqual(stats.get("fluency_rating"), 0.0)
        self.assertEqual(stats.get("count"), 0)
        self.assertEqual(stats.get("streak"), 0)
        self.assertEqual(stats.get("percentile"), 0)

    def test_dashboard_with_data(self):
        """
        If the user has events and feedback in the past week/month, ensure
        the endpoint averages them and includes them in the response.
        """
        self.client.force_authenticate(user=self.user)

        # Create some Feedback
        now = timezone.now()
        Feedback.objects.create(
            user=self.user_profile,
            azure_id="123e4567-e89b-12d3-a456-426614174000",
            display_text="Test text",
            accuracy_score=80.0,
            fluency_score=85.0,
            completeness_score=90.0,
            pron_score=82.0,
            timestamp=now,
        )
        Feedback.objects.create(
            user=self.user_profile,
            azure_id="00000000-0000-0000-0000-000000000000",
            display_text="Old text",
            accuracy_score=10.0,
            fluency_score=10.0,
            completeness_score=10.0,
            pron_score=10.0,
            timestamp=now - timedelta(days=20),
        )

        # Create some Events
        Event.objects.create(
            user=self.user_profile,
            event_type="PRACTICE_PRON",
            timestamp=now
        )
        Event.objects.create(
            user=self.user_profile,
            event_type="OTHER_EVENT",
            timestamp=now - timedelta(days=1)
        )
        Event.objects.create(
            user=self.user_profile,
            event_type="PRACTICE_PRON",
            timestamp=now - timedelta(days=4)
        )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.data.get("progress_dashboard", {})
        stats = data.get("stats", {})

        self.assertAlmostEqual(stats.get("overall"), 46.17, places=2)
        self.assertAlmostEqual(stats.get("fluency_rating"), 46.17, places=2)
        self.assertEqual(stats.get("count"), 3)
        self.assertEqual(stats.get("streak"), 1)
        self.assertEqual(stats.get("percentile"), 0)
        self.assertEqual(week_fluency, 47.5)
        self.assertEqual(week_pronunciation, 46.0)
        self.assertEqual(week_accuracy, 45.0)

    def test_dashboard_streak(self):
        """
        Verify that the streak is computed as consecutive days with events.
        """
        self.client.force_authenticate(user=self.user)

        now = timezone.now()
        Event.objects.create(user=self.user_profile, event_type="PRACTICE_PRON", timestamp=now)
        Event.objects.create(
            user=self.user_profile,
            event_type="PRACTICE_PRON",
            timestamp=now - timedelta(days=1)
        )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        streak = response.data["progress_dashboard"]["stats"]["streak"]
        self.assertEqual(streak, 1)
