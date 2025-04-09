import logging as logger

from django.urls import path
from django.http import HttpResponse

from . import views


def trigger_error(_request):
    """
    Trigger an error to test Sentry
    """
    logger.error("Sentry Backend Example Error")
    response = HttpResponse("Sentry Backend Example Error", status=500)
    return response


urlpatterns = [
    path("sentry-debug/", trigger_error),
    path("", views.index.as_view(), name="index"),
]
