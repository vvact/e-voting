from rest_framework import serializers
from .models import Vote, Candidate, Position, Election,PoliticalParty



class PoliticalPartySerializer(serializers.ModelSerializer):
    badge_url = serializers.SerializerMethodField()

    class Meta:
        model = PoliticalParty
        fields = ["id", "name", "abbreviation", "badge", "badge_url"]

    def get_badge_url(self, obj):
        request = self.context.get("request")
        if obj.badge and request:
            return request.build_absolute_uri(obj.badge.url)
        return None

# =========================
# Candidate Serializer
# =========================
class CandidateSerializer(serializers.ModelSerializer):
    total_votes = serializers.IntegerField(source="vote_set.count", read_only=True)
    photo_url = serializers.SerializerMethodField()
    party = PoliticalPartySerializer(read_only=True)

    class Meta:
        model = Candidate
        fields = [
            "id",
            "full_name",
            "party",
            "position",
            "photo",
            "photo_url",
            "total_votes",
        ]

    def get_photo_url(self, obj):
        request = self.context.get("request")

        if obj.photo and hasattr(obj.photo, "url"):
            if request:
                return request.build_absolute_uri(obj.photo.url)
            return obj.photo.url

        return None


# =========================
# Position Serializer
# =========================
class PositionSerializer(serializers.ModelSerializer):
    candidates = CandidateSerializer(many=True, read_only=True)

    class Meta:
        model = Position
        fields = ["id", "title", "election", "candidates"]


# =========================
# Election Serializer
# =========================
class ElectionSerializer(serializers.ModelSerializer):
    positions = PositionSerializer(many=True, read_only=True)

    class Meta:
        model = Election
        fields = ["id", "name", "start_time", "end_time", "is_active", "positions"]


# =========================
# Vote Serializer
# =========================
class VoteSerializer(serializers.ModelSerializer):
    candidate_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Vote
        fields = ["candidate_id"]

    def validate(self, data):
        candidate_id = data.get("candidate_id")

        try:
            candidate = Candidate.objects.select_related("position").get(
                id=candidate_id
            )
        except Candidate.DoesNotExist:
            raise serializers.ValidationError("Candidate not found")

        # Attach candidate object
        data["candidate"] = candidate
        data["position"] = candidate.position  # 🔥 IMPORTANT
        return data
