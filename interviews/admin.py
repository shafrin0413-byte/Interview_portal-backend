from django.contrib import admin
from .models import Interview, InterviewFeedback, CandidateDecision

admin.site.register(Interview)
admin.site.register(InterviewFeedback)
admin.site.register(CandidateDecision)
