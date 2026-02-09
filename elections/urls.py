from django.urls import path
from .views import CastVoteView
from .views import ElectionResultsView

urlpatterns = [
    path("vote/", CastVoteView.as_view(), name="cast-vote"),
    path('results/', ElectionResultsView.as_view(), name='election-results'),
]
