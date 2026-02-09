from django.db import models
from django.utils import timezone
from django.conf import settings


class Election(models.Model):
    name = models.CharField(max_length=255)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_active = models.BooleanField(default=False)

    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name


class Position(models.Model):
    election = models.ForeignKey(
        Election,
        on_delete=models.CASCADE,
        related_name="positions"
    )
    title = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.title} - {self.election.name}"


class Candidate(models.Model):
    position = models.ForeignKey(
        Position,
        on_delete=models.CASCADE,
        related_name="candidates"
    )
    full_name = models.CharField(max_length=255)
    party = models.CharField(max_length=255, blank=True, null=True)
    photo = models.ImageField(upload_to="candidates/", blank=True, null=True)

    def __str__(self):
        return f"{self.full_name} ({self.position.title})"


class Vote(models.Model):
    voter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    position = models.ForeignKey(
        Position,
        on_delete=models.CASCADE
    )
    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE
    )
    voted_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ['voter', 'position']

    def __str__(self):
        return f"{self.voter.email} voted for {self.candidate.full_name} ({self.position.title})"
