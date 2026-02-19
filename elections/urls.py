from django.urls import path
from .views import CastVoteView
from .views import ElectionResultsView
from .views import (
    ElectionListView,
    ActiveElectionsView,
    UpcomingElectionsView,
    ClosedElectionsView,
    ElectionStatsView,
    ElectionDetailView,
)


urlpatterns = [
    path("vote/", CastVoteView.as_view(), name="cast-vote"),
    path("results/", ElectionResultsView.as_view(), name="election-results"),
    path("elections/", ElectionListView.as_view()),
    path("active/", ActiveElectionsView.as_view()),
    path("upcoming/", UpcomingElectionsView.as_view()),
    path("closed/", ClosedElectionsView.as_view()),
    path("stats/", ElectionStatsView.as_view()),
    path("elections/<int:pk>/", ElectionDetailView.as_view()),
]
