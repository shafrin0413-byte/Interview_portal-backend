from django.contrib import admin
from .models import Assessment, Question, AssessmentAssignment, AssessmentResult

admin.site.register(Assessment)
admin.site.register(Question)
admin.site.register(AssessmentAssignment)
admin.site.register(AssessmentResult)
