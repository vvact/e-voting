from django.urls import path
from .views import CastVoteView

urlpatterns = [
    path("vote/", CastVoteView.as_view(), name="cast-vote"),
]
