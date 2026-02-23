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

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone

from .models import Vote, Election
from .serializers import VoteSerializer

User = get_user_model()


# =========================
# Cast Vote
# =========================
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from .models import Vote, Candidate, Position, Election
from .serializers import VoteSerializer

class CastVoteView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        user = request.user

        # 1️⃣ Check if user is verified
        if not getattr(user, "is_verified", False):
            return Response(
                {"error": "Account not verified"},
                status=status.HTTP_403_FORBIDDEN
            )

        # 2️⃣ Validate input
        serializer = VoteSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        candidate = serializer.validated_data["candidate"]
        position = serializer.validated_data["position"]
        election = serializer.validated_data["election"]

        # 3️⃣ Prevent double voting per position
        if Vote.objects.filter(voter=user, position=position).exists():
            return Response(
                {"error": f"You already voted for {position.title}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 4️⃣ Create the vote
        vote = Vote.objects.create(
            voter=user,
            candidate=candidate,
            position=position,
            election=election,
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", "")
        )

        # 5️⃣ Mark user as voted for this position (for frontend/admin)
        # Option A: using a ManyToMany on Position
        position.voters.add(user)
        position.save()

        # 6️⃣ Update candidate's vote count
        candidate.total_votes = candidate.total_votes + 1
        candidate.save()

        return Response(
            {"message": f"Vote cast successfully for {position.title}"},
            status=status.HTTP_201_CREATED
        )

    def get_client_ip(self, request):
        """Optional helper to store voter IP"""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip
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
    lookup_field = "slug"

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
