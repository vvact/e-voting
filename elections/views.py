from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models import Count

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status

from .models import Vote, Election, Position
from .serializers import VoteSerializer, ElectionSerializer

from rest_framework import generics
from rest_framework.permissions import AllowAny
from .models import Election
from .serializers import ElectionSerializer

User = get_user_model()


# =========================
# Cast Vote
# =========================
class CastVoteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        # 1️⃣ Check if verified
        if not getattr(user, "is_verified", False):
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
                    status=status.HTTP_400_BAD_REQUEST,
                )
                
            

            # 5️⃣ Save vote
            Vote.objects.create(voter=user, candidate=candidate, position=position)

            return Response(
                {"message": f"Vote cast successfully for {position.title}"},
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# =========================
# Election Results
# =========================
class ElectionResultsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        election = Election.objects.filter(is_active=True).first()
        if not election:
            return Response({"message": "No active election", "results": []})

        results = []

        positions = election.positions.prefetch_related(
            "candidates__party"
        )

        for position in positions:
            candidates = position.candidates.annotate(
                total_votes=Count("vote")
            ).order_by("-total_votes")

            candidates_data = []

            for candidate in candidates:
                candidates_data.append({
                    "candidate_id": candidate.id,
                    "full_name": candidate.full_name,
                    "party": {
                        "id": candidate.party.id if candidate.party else None,
                        "name": candidate.party.name if candidate.party else None,
                        "badge_url": request.build_absolute_uri(candidate.party.badge.url)
                        if candidate.party and candidate.party.badge
                        else None,
                    },
                    "votes": candidate.total_votes,
                })

            results.append({
                "position": position.title,
                "candidates": candidates_data
            })

        return Response({
            "election": election.name,
            "results": results
        })

# =========================
# Election List
# =========================
class ElectionListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        elections = Election.objects.prefetch_related(
            "positions__candidates__party"
        ).order_by("-start_time")

        serializer = ElectionSerializer(
            elections,
            many=True,
            context={"request": request}
        )
        return Response(serializer.data)


class ElectionDetailView(generics.RetrieveAPIView):
    serializer_class = ElectionSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Election.objects.prefetch_related(
            "positions__candidates__party"
        )

    def get_serializer_context(self):
        return {"request": self.request}

# =========================
# Active Elections
# =========================
class ActiveElectionsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        now = timezone.now()
        elections = Election.objects.filter(
            start_time__lte=now,
            end_time__gte=now
        ).order_by("end_time")
        serializer = ElectionSerializer(elections, many=True, context={"request": request})
        return Response(serializer.data)


# =========================
# Upcoming Elections
# =========================
class UpcomingElectionsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        now = timezone.now()
        elections = Election.objects.filter(start_time__gt=now).order_by("start_time")
        serializer = ElectionSerializer(elections, many=True, context={"request": request})
        return Response(serializer.data)


# =========================
# Closed Elections
# =========================
class ClosedElectionsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        now = timezone.now()
        elections = Election.objects.filter(end_time__lt=now).order_by("-end_time")
        serializer = ElectionSerializer(elections, many=True, context={"request": request})
        return Response(serializer.data)


# =========================
# Election Stats
# =========================
class ElectionStatsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        now = timezone.now()

        total_elections = Election.objects.count()
        active_elections = Election.objects.filter(
            start_time__lte=now, end_time__gte=now
        ).count()
        total_votes = Vote.objects.count()
        total_voters = User.objects.count()

        return Response({
            "total_elections": total_elections,
            "active_elections": active_elections,
            "total_votes": total_votes,
            "total_voters": total_voters,
        })
