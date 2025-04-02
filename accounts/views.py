from django.contrib.auth import login, get_user_model
from rest_framework import (
    exceptions,
    permissions,
    response,
    serializers,
    status,
    views,
)
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.settings import api_settings
from drf_spectacular.utils import extend_schema, inline_serializer
import knox.views

from . import models, decorators
from .serializers import SignUpRequestSerializer


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
