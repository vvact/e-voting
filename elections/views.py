from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.utils import timezone

from .models import Vote, Candidate, Election
from .serializers import VoteSerializer



class CastVoteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        # 1️⃣ Check if verified
        if not user.is_verified:
            return Response(
                {"error": "Account not verified"},
                status=status.HTTP_403_FORBIDDEN
            )

        # 2️⃣ Prevent double voting
        if user.has_voted:
            return Response(
                {"error": "You have already voted"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 3️⃣ Check active election
        election = Election.objects.filter(is_active=True).first()

        if not election:
            return Response(
                {"error": "No active election"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 4️⃣ Validate candidate
        serializer = VoteSerializer(data=request.data)

        if serializer.is_valid():
            candidate = serializer.validated_data["candidate"]

            # 5️⃣ Save vote
            Vote.objects.create(
                voter=user,
                candidate=candidate
            )

            # 6️⃣ Mark user as voted
            user.has_voted = True
            user.save(update_fields=["has_voted"])

            return Response(
                {"message": "Vote cast successfully"},
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
