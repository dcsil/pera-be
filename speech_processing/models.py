from django.db import models

import texts.models
import accounts.models


class Feedback(models.Model):
    feedback_id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(
        accounts.models.UserProfile, on_delete=models.CASCADE, null=True
    )
    sentence = models.ForeignKey(
        texts.models.Sentence, on_delete=models.CASCADE, null=True
    )
    azure_id = models.UUIDField()
    display_text = models.TextField()
    accuracy_score = models.FloatField()
    fluency_score = models.FloatField()
    completeness_score = models.FloatField()
    pron_score = models.FloatField()
    json_data = models.JSONField(null=True)
    timestamp = models.DateTimeField(null=True, auto_now=True)
    created_at = models.DateTimeField(null=True, auto_now=True)

    def __str__(self):
        return f"Feedback #{self.feedback_id}, on sentence #{self.sentence_id}, displaying {self.display_text}"


class Error(models.Model):
    error_id = models.BigAutoField(primary_key=True)
    feedback = models.ForeignKey(Feedback, on_delete=models.CASCADE, null=True)
    phoneme = models.TextField()
    syllable = models.TextField()
    accuracy_score = models.FloatField()
    error_type = models.TextField()
    error_text = models.TextField()
    created_at = models.DateTimeField(null=True, auto_now=True)

    def __str__(self):
        return f"Error #{self.error_id}, on feedback #{self.feedback_id}, of type {self.error_type}"
