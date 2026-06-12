from django.contrib import admin
from .models import CandidateProfile, Resume, Skill, Education, Experience

admin.site.register(CandidateProfile)
admin.site.register(Resume)
admin.site.register(Skill)
admin.site.register(Education)
admin.site.register(Experience)
