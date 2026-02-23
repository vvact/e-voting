from django.db import models
from django.utils import timezone
from django.conf import settings
from django.utils.text import slugify
import uuid

from accounts.models import User


class Election(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_active = models.BooleanField(default=False)

    created_at = models.DateTimeField(default=timezone.now)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            while Election.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{uuid.uuid4().hex[:4]}"
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Position(models.Model):
    # Track voters
    voters = models.ManyToManyField(User, blank=True)
    election = models.ForeignKey(
        Election, on_delete=models.CASCADE, related_name="positions"
    )
    title = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.title} - {self.election.name}"


class PoliticalParty(models.Model):
    name = models.CharField(max_length=100, unique=True)
    abbreviation = models.CharField(max_length=20, blank=True)
    badge = models.ImageField(upload_to="party_badges/")

    def __str__(self):
        return self.name

class Candidate(models.Model):
    position = models.ForeignKey(
        Position, on_delete=models.CASCADE, related_name="candidates"
    )
    full_name = models.CharField(max_length=255)
    party = models.ForeignKey(PoliticalParty, on_delete=models.SET_NULL, null=True, blank=True)
    photo = models.ImageField(upload_to="candidates/", blank=True, null=True)

    def __str__(self):
        return f"{self.full_name} ({self.position.title})"
    



# models.py
class Vote(models.Model):
    voter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    election = models.ForeignKey("Election", on_delete=models.CASCADE, related_name="votes")
    position = models.ForeignKey("Position", on_delete=models.CASCADE)
    candidate = models.ForeignKey("Candidate", on_delete=models.CASCADE)
    voted_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=[("valid","Valid"),("invalid","Invalid")], default="valid")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        unique_together = ["voter", "position"]
