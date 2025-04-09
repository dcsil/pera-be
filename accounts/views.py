from django.contrib.auth import login, get_user_model
from rest_framework import (
    exceptions,
    permissions,
    response,
    serializers,
    views,
)
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.settings import api_settings
from drf_spectacular.utils import extend_schema, inline_serializer
import knox.views

from . import models, decorators
from .serializers import SignUpRequestSerializer
from .decorators import require_authentication
import datetime
from django.db.models import Avg, Count, Q
from django.utils import timezone
from speech_processing.models import Feedback
from .models import Event
from django.db.models.functions import TruncDate

class SignUpView(views.APIView):
    serializer_class = SignUpRequestSerializer

    @extend_schema(
        responses={
            200: inline_serializer(
                "SignUpResponseSerializer",
                fields={
                    "success": serializers.BooleanField(),
                    "message": serializers.CharField(required=False),
                },
            )
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data
        UserManager = get_user_model().objects
        if UserManager.all().filter(email=d["email"]).count() > 0:
            return response.Response(
                {"success": False, "message": "Email already in use."},
                status=200,
            )
        user = UserManager.create_user(d["email"], d["password"])
        user.name = d["name"]
        profile = models.UserProfile(
            auth_user=user,
            default_settings={},
            base_language=d["base_language"],
        )
        user.save()
        profile.save()
        return response.Response({"success": True}, status=200)


# see https://jazzband.github.io/django-rest-knox/auth/#global-usage-on-all-views
# I also added 401, just copy-pasting from them gives 400 on failed login


@decorators.extend_schema_auth_failed
class LoginView(knox.views.LoginView):
    """Note that email is used as the username."""

    permission_classes = (permissions.AllowAny,)
    serializer_class = AuthTokenSerializer

    # see https://github.com/jazzband/django-rest-knox/blob/develop/knox/views.py
    @extend_schema(
        responses={
            200: inline_serializer(
                "LoginResponse",
                fields={
                    "expiry": serializers.CharField(),
                    "token": serializers.CharField(),
                },
            )
        },
    )
    def post(self, request, format=None):
        try:
            serializer = self.serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)
        except serializers.ValidationError as e:
            # see https://github.com/encode/django-rest-framework/blob/master/rest_framework/authtoken/serializers.py
            # also https://www.django-rest-framework.org/api-guide/exceptions/, in the first section
            if api_settings.NON_FIELD_ERRORS_KEY in e.detail:
                # should be able to do e.detail[key][0] right away, this is just for my sanity
                for detail in e.detail[api_settings.NON_FIELD_ERRORS_KEY]:
                    if detail.code == "authorization":
                        raise exceptions.AuthenticationFailed(detail)
            raise
        user = serializer.validated_data["user"]
        login(request, user)
        return super(LoginView, self).post(request, format)


@decorators.extend_schema_auth_failed
class LogoutView(knox.views.LogoutView):
    @extend_schema(request=None, responses={204: None})
    def post(self, request, format=None):
        return super(LogoutView, self).post(request, format)


@decorators.extend_schema_auth_failed
class LogoutAllView(knox.views.LogoutAllView):
    @extend_schema(request=None, responses={204: None})
    def post(self, request, format=None):
        return super(LogoutAllView, self).post(request, format)


@require_authentication()
class DashboardView(views.APIView):

    def get(self, request):
        user_profile = request.user.userprofile
        now = timezone.now()

        one_week_ago = now - datetime.timedelta(days=7)
        one_month_ago = now - datetime.timedelta(days=30)

        week_feedback_qs = Feedback.objects.filter(
            user=user_profile,
            timestamp__gte=one_week_ago
        )
        month_feedback_qs = Feedback.objects.filter(
            user=user_profile,
            timestamp__gte=one_month_ago
        )

        week_feedback = week_feedback_qs.aggregate(
            week_accuracy=Avg("accuracy_score"),
            week_fluency=Avg("fluency_score"),
            week_pronunciation=Avg("pron_score")
        )
        if week_feedback["week_accuracy"] and week_feedback["week_fluency"] and week_feedback["week_pronunciation"]:
            week_overall = (
                week_feedback["week_accuracy"]
                + week_feedback["week_fluency"]
                + week_feedback["week_pronunciation"]
            ) / 3
        else:
            week_overall = 0.0

        month_feedback = month_feedback_qs.aggregate(
            month_accuracy=Avg("accuracy_score"),
            month_fluency=Avg("fluency_score"),
            month_pronunciation=Avg("pron_score")
        )
        if month_feedback["month_accuracy"] and month_feedback["month_fluency"] and month_feedback["month_pronunciation"]:
            month_overall = (
                month_feedback["month_accuracy"]
                + month_feedback["month_fluency"]
                + month_feedback["month_pronunciation"]
            ) / 3
        else:
            month_overall = 0.0

        total_events_count = Event.objects.filter(user=user_profile).count()

        events_dates = Event.objects.filter(user=user_profile).values_list("timestamp", flat=True)
        unique_days = {dt.date() for dt in events_dates}

        streak_count = 0
        start_date = now.date()

        # If there's no event for today, start from yesterday instead
        if start_date not in unique_days:
            start_date -= datetime.timedelta(days=1)

        while start_date in unique_days:
            streak_count += 1
            start_date -= datetime.timedelta(days=1)


        week_pron_exercises_count = Event.objects.filter(
            user=user_profile,
            event_type="PRACTICE_PRON",
            timestamp__gte=one_week_ago
        ).count()

        all_users = Feedback.objects.filter(timestamp__gte=one_week_ago)
        # Calculate per-user averages for the last week
        all_users = (
            all_users.values("user")
            .annotate(
                avg_score=(
                    (Avg("accuracy_score") + Avg("fluency_score") + Avg("pron_score")) / 3
                )
            )
        )

        # Compute overall average for each user in the last week
        user_averages = (
            all_users.values("user")
            .annotate(
                avg_score=(
                    (Avg("accuracy_score") + Avg("fluency_score") + Avg("pron_score")) / 3
                )
            )
        )
        # See how many have an avg_score < user’s
        lower_count = sum(1 for ua in user_averages if ua["avg_score"] < week_overall)
        total_count = len(user_averages)
        percentile = (lower_count / total_count * 100) if total_count > 0 else 0

        daily_stats = (
            week_feedback_qs
            .annotate(date=TruncDate("timestamp"))
            .values("date")
            .annotate(
                daily_accuracy=Avg("accuracy_score"),
                daily_fluency=Avg("fluency_score"),
                daily_pron=Avg("pron_score"),
            )
            .order_by("date")
        )
        data_list = []
        for day in daily_stats:
            data_list.append({
                "date": str(day["date"]),
                "accuracy": day["daily_accuracy"] or 0,
                "fluency": day["daily_fluency"] or 0,
                "pronunciation": day["daily_pron"] or 0
            })

        response_data = {
            "progress_dashboard": {
                "stats": {
                    "overall": round(week_overall, 2),
                    "fluency_rating": round(month_overall, 2),
                    "count": total_events_count,
                    "streak": streak_count,
                    "week_fluency": round(week_feedback["week_fluency"] or 0, 2),
                    "week_accuracy": round(week_feedback["week_accuracy"] or 0, 2),
                    "week_pronunciation": round(week_feedback["week_pronunciation"] or 0, 2),
                    "week_reading_exercises": 3,   # Hardcoded
                    "week_conversation_exercises": 2,  # Hardcoded
                    "week_pronunciation_exercises": week_pron_exercises_count,
                    "percentile": int(percentile),
                },
                "data": data_list
            }
        }

        return response.Response(response_data, status=200)
