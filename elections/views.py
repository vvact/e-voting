from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .models import Vote, Election
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

        # 2️⃣ Check active election
        election = Election.objects.filter(is_active=True).first()
        if not election:
            return Response(
                {"error": "No active election"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 3️⃣ Validate input
        serializer = VoteSerializer(data=request.data)
        if serializer.is_valid():
            candidate = serializer.validated_data["candidate"]
            position = serializer.validated_data["position"]

            # 4️⃣ Prevent double voting PER POSITION
            if Vote.objects.filter(voter=user, position=position).exists():
                return Response(
                    {"error": f"You already voted for {position.title}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 5️⃣ Save vote
            Vote.objects.create(
                voter=user,
                candidate=candidate,
                position=position
            )

            return Response(
                {"message": f"Vote cast successfully for {position.title}"},
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
