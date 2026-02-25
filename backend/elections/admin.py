from django.contrib import admin
from django.utils.html import format_html
from django.db import models
from .models import Election, Position, Candidate, Vote,PoliticalParty




@admin.register(PoliticalParty)
class PoliticalPartyAdmin(admin.ModelAdmin):
    list_display = ("name", "abbreviation")
# =========================
# ELECTION ADMIN
# =========================
@admin.register(Election)
class ElectionAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "start_time",
        "end_time",
        "is_active",
        "created_at",
    )

    search_fields = ("name",)
    list_filter = ("is_active",)
    ordering = ("-created_at",)
    readonly_fields = ("created_at",)


# =========================
# POSITION ADMIN
# =========================
from django.contrib import admin
from django.core.cache import cache
from .models import Position, Candidate

@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ("title", "election", "total_votes")
    search_fields = ("title",)
    list_filter = ("election",)
    exclude = ("voters",)  # hide the voters multi-select

    def total_votes(self, obj):
        """
        Show total votes for this position by summing live votes for all its candidates from Redis.
        """
        total = 0
        for candidate in obj.candidates.all():
            redis_key = f"live_votes_{candidate.id}"
            total += cache.get(redis_key, candidate.total_votes)
        return total

    total_votes.short_description = "Total Votes"


# =========================
# CANDIDATE ADMIN
# =========================
@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "position",
        "party",
        "highlight_votes",  # shows votes + highlights top candidate
    )

    search_fields = ("full_name", "party")
    list_filter = ("position",)

    def total_votes(self, obj):
        return Vote.objects.filter(candidate=obj).count()

    total_votes.short_description = "Total Votes"

    def highlight_votes(self, obj):
        votes = self.total_votes(obj)

        max_votes = (
            Vote.objects.filter(position=obj.position)
            .values_list("candidate")
            .annotate(count=models.Count("id"))
            .order_by("-count")
            .first()
        )

        if max_votes and max_votes[0] == obj.id:
            return format_html('<b style="color:green;">{} ✅</b>', votes)
        return votes

    highlight_votes.short_description = "Total Votes"
    highlight_votes.admin_order_field = None  # safe for now

    class Media:
        css = {"all": ("admin_css/custom.css",)}


# =========================
# VOTE ADMIN (SECURE)
# =========================
@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = (
        "voter",
        "candidate",
        "position",
        "voted_at",
    )

    search_fields = (
        "voter__email",
        "candidate__full_name",
    )

    list_filter = ("position",)
    ordering = ("-voted_at",)
    readonly_fields = ("voter", "candidate", "position", "voted_at")

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
