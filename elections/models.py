from django.db import models
from django.utils import timezone


class Election(models.Model):
    name = models.CharField(max_length=255)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_active = models.BooleanField(default=False)

    def has_started(self):
        return timezone.now() >= self.start_time

    def has_ended(self):
        return timezone.now() > self.end_time

    def __str__(self):
        return self.name


class Position(models.Model):
    name = models.CharField(max_length=100)
    election = models.ForeignKey(
        Election,
        on_delete=models.CASCADE,
        related_name="positions"
    )

    def __str__(self):
        return f"{self.name} ({self.election.name})"


class Candidate(models.Model):
    name = models.CharField(max_length=255)
    position = models.ForeignKey(
        Position,
        on_delete=models.CASCADE,
        related_name="candidates"
    )

    manifesto = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} - {self.position.name}"

