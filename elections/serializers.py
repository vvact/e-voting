from rest_framework import serializers
from .models import Vote, Candidate


class VoteSerializer(serializers.ModelSerializer):
    candidate_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Vote
        fields = ['candidate_id']

    def validate(self, data):
        candidate_id = data.get("candidate_id")

        try:
            candidate = Candidate.objects.get(id=candidate_id)
        except Candidate.DoesNotExist:
            raise serializers.ValidationError("Candidate not found")

        data["candidate"] = candidate
        return data
