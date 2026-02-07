
from django.contrib import admin
from .models import Election, Position, Candidate, Vote


admin.site.register(Election)
admin.site.register(Position)
admin.site.register(Candidate)
admin.site.register(Vote)
