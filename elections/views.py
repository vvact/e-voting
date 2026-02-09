from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .models import Vote, Election
from .serializers import VoteSerializer

from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Position, Vote


from django.db.models import Count
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Position



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
    
    



from django.db.models import Count
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Position


from django.db.models import Count
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Position, Election


class ElectionResultsView(APIView):

    permission_classes = []  # PUBLIC ACCESS

    def get(self, request):

        # 1️⃣ Get active election
        election = Election.objects.filter(is_active=True).first()

        if not election:
            return Response({
                "message": "No active election",
                "results": []
            })

        results = []

        # 2️⃣ Get positions for this election only
        positions = election.positions.prefetch_related('candidates')

        for position in positions:

            # 3️⃣ Count votes per candidate
            candidates = position.candidates.annotate(
                total_votes=Count('vote')
            ).order_by('-total_votes')

            candidates_data = []

            for candidate in candidates:
                candidates_data.append({
                    "candidate_id": candidate.id,
                    "full_name": candidate.full_name,
                    "party": candidate.party,
                    "votes": candidate.total_votes
                })

            results.append({
                "position": position.title,
                "candidates": candidates_data
            })

        return Response({
            "election": election.name,
            "results": results
        })


