from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    """
    Although in the schema there is one Users table, I split it into two here,
    specifically, `authtools.User` and `accounts.UserProfile` (this).
    The reason is that `authtools.User` contains actual authentication functionality,
    which is something we need. The general recommendation django and django-authtools
    devs suggest is what I've done here, which is to add a profile table with a
    one-to-one relation with the auth User table. Then this is the one which links to
    all app functionality like events and passages.
    """

    auth_user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, primary_key=True
    )

    default_settings = models.JSONField()
    base_language = models.CharField(max_length=50)

    def __str__(self):
        return f"User profile for {self.auth_user.name}, email {self.auth_user.email}"


class Event(models.Model):
    event_id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, null=True)
    event_type = models.CharField(max_length=100)
    timestamp = models.DateTimeField(null=True, auto_now=True)
    created_at = models.DateTimeField(null=True, auto_now=True)

    def __str__(self):
        return f"Event of type {self.event_type} on user {self.user_id} on {self.timestamp}"
