from django.db import models

import accounts.models


class Passage(models.Model):
    passage_id = models.BigAutoField(primary_key=True)
    user_id = models.ForeignKey(
        accounts.models.UserProfile, on_delete=models.CASCADE, null=True
    )
    language = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    difficulty = models.CharField(max_length=50)
    created_at = models.DateTimeField(null=True, auto_now=True)

    def __str__(self):
        return f"Passage #{self.passage_id}, by user {self.user_id}, with title '{self.title}'"


class Sentence(models.Model):
    sentence_id = models.BigAutoField(primary_key=True)
    passage_id = models.ForeignKey(
        Passage, on_delete=models.CASCADE, null=True
    )
    text = models.TextField()
    completion_status = models.BooleanField(null=True)
    created_at = models.DateTimeField(null=True, auto_now=True)

    def __str__(self):
        return f"Sentence #{self.sentence_id}, from passage #{self.passage_id}, with text '{self.text}'"
