from django.contrib import admin
from .models import ResumeAnalysis, JobMatch, CandidateRanking, AIQuestion

admin.site.register(ResumeAnalysis)
admin.site.register(JobMatch)
admin.site.register(CandidateRanking)
admin.site.register(AIQuestion)
