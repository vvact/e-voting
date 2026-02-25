from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models import Count
from django.db import transaction

from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from django.core.cache import cache

from .models import Vote, Election, Position, Candidate
from .serializers import VoteSerializer, ElectionSerializer

User = get_user_model()


# =========================
# Cast Vote
# =========================
class CastVoteView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        user = request.user

        # 1️⃣ Check if user is verified
        if not getattr(user, "is_verified", False):
            return Response({"error": "Account not verified"},
                            status=status.HTTP_403_FORBIDDEN)

        # 2️⃣ Validate input
        serializer = VoteSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        candidate = serializer.validated_data["candidate"]
        position = serializer.validated_data["position"]
        election = serializer.validated_data["election"]

        # 3️⃣ Prevent double voting per position using Redis
        redis_key_voted = f"voted_{user.id}_{position.id}"
        if cache.get(redis_key_voted) or Vote.objects.filter(voter=user, position=position).exists():
            return Response({"error": f"You already voted for {position.title}"},
                            status=status.HTTP_400_BAD_REQUEST)

        # 4️⃣ Create the vote
        vote = Vote.objects.create(
            voter=user,
            candidate=candidate,
            position=position,
            election=election,
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", "")
        )

        # 5️⃣ Mark as voted in Redis for 1 hour
        cache.set(redis_key_voted, True, timeout=3600)

        # 6️⃣ Increment candidate vote count in DB
        candidate.total_votes = candidate.total_votes + 1
        candidate.save()

        # 7️⃣ Increment live vote count in Redis
        redis_key_live = f"live_votes_{candidate.id}"
        cache.incr(redis_key_live, default=candidate.total_votes)

        return Response({
            "message": f"Vote cast successfully for {position.title}",
            "candidate_id": candidate.id,
            "live_votes": cache.get(redis_key_live)
        }, status=status.HTTP_201_CREATED)

    def get_client_ip(self, request):
        """Optional helper to store voter IP"""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip

# =========================
# Election List & Detail with Redis
# =========================
class ElectionListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        elections = Election.objects.prefetch_related(
            "positions__candidates__party"
        ).order_by("-start_time")
        serializer = ElectionSerializer(elections, many=True, context={"request": request})
        return Response(serializer.data)


class ElectionDetailView(generics.RetrieveAPIView):
    serializer_class = ElectionSerializer
    permission_classes = [AllowAny]
    authentication_classes = []
    lookup_field = "slug"

    def get_queryset(self):
        return Election.objects.prefetch_related(
            "positions__candidates__party"
        )

    def get_serializer_context(self):
        return {"request": self.request}

    def retrieve(self, request, *args, **kwargs):
        slug = self.kwargs.get(self.lookup_field)
        cache_key = f"election_{slug}"

        # Check Redis cache first
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)

        election = self.get_object()
        serializer = self.get_serializer(election)
        data = serializer.data

        # Cache serialized data for 60 seconds
        cache.set(cache_key, data, timeout=60)
        return Response(data)


# =========================
# Candidate List per Position (Cached)
# =========================
class CandidateListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, election_slug=None, position_slug=None):
        cache_key = f"candidates_{election_slug}_{position_slug}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)

        candidates = Candidate.objects.filter(
            position__slug=position_slug,
            position__election__slug=election_slug
        ).select_related("party", "position")

        serializer = VoteSerializer(candidates, many=True, context={"request": request})
        data = serializer.data

        # Cache candidates for 2 minutes
        cache.set(cache_key, data, timeout=120)
        return Response(data)


# =========================
# Election Status Views
# =========================
class ActiveElectionsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        now = timezone.now()
        elections = Election.objects.filter(
            start_time__lte=now, end_time__gte=now
        ).order_by("end_time")
        serializer = ElectionSerializer(elections, many=True, context={"request": request})
        return Response(serializer.data)


class UpcomingElectionsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        now = timezone.now()
        elections = Election.objects.filter(start_time__gt=now).order_by("start_time")
        serializer = ElectionSerializer(elections, many=True, context={"request": request})
        return Response(serializer.data)


class ClosedElectionsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        now = timezone.now()
        elections = Election.objects.filter(end_time__lt=now).order_by("-end_time")
        serializer = ElectionSerializer(elections, many=True, context={"request": request})
        return Response(serializer.data)


# =========================
# Election Results
# =========================
class ElectionResultsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        # Only one active election at a time
        election = Election.objects.filter(is_active=True).first()
        if not election:
            return Response({"message": "No active election", "results": []})

        cache_key = f"results_{election.id}"
        cached_results = cache.get(cache_key)

        if cached_results:
            # Update live votes from Redis
            for position_data in cached_results:
                for candidate_data in position_data["candidates"]:
                    redis_key = f"live_votes_{candidate_data['candidate_id']}"
                    candidate_data["votes"] = cache.get(redis_key, candidate_data["votes"])
            return Response({
                "election": election.name,
                "results": cached_results
            })

        # If not cached, generate results
        results = []

        positions = election.positions.prefetch_related("candidates__party")

        for position in positions:
            candidates_data = []

            for candidate in position.candidates.all():
                # Live votes from Redis or fallback to DB
                redis_key = f"live_votes_{candidate.id}"
                live_votes = cache.get(redis_key, candidate.total_votes)

                candidates_data.append({
                    "candidate_id": candidate.id,
                    "full_name": candidate.full_name,
                    "party": {
                        "id": candidate.party.id if candidate.party else None,
                        "name": candidate.party.name if candidate.party else None,
                        "badge_url": request.build_absolute_uri(candidate.party.badge.url)
                        if candidate.party and candidate.party.badge else None,
                    },
                    "votes": live_votes,
                })

            # Sort candidates by live votes
            candidates_data.sort(key=lambda x: x["votes"], reverse=True)

            results.append({
                "position": position.title,
                "candidates": candidates_data
            })

        # Cache entire results for 30 seconds
        cache.set(cache_key, results, timeout=30)

        return Response({
            "election": election.name,
            "results": results
        })
# =========================
# Election Stats
# =========================
class ElectionStatsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        now = timezone.now()
        return Response({
            "total_elections": Election.objects.count(),
            "active_elections": Election.objects.filter(
                start_time__lte=now, end_time__gte=now
            ).count(),
            "total_votes": Vote.objects.count(),
            "total_voters": User.objects.count(),
        })