from rest_framework import serializers
from .models import Job, Application
from accounts.serializers import UserSerializer
from candidates.serializers import CandidateProfileSerializer


class JobSerializer(serializers.ModelSerializer):
    recruiter_name = serializers.CharField(source='recruiter.username', read_only=True)
    application_count = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = ('id', 'recruiter', 'recruiter_name', 'title', 'company', 'location',
                  'work_mode', 'job_type', 'experience', 'salary',
                  'description', 'requirements', 'skills_required', 'status',
                  'expires_at', 'application_count', 'created_at')
        read_only_fields = ('recruiter',)

    def get_application_count(self, obj):
        return obj.applications.count()


class ApplicationSerializer(serializers.ModelSerializer):
    candidate = CandidateProfileSerializer(read_only=True)
    job_title = serializers.CharField(source='job.title', read_only=True)
    job_company = serializers.CharField(source='job.company', read_only=True)

    class Meta:
        model = Application
        fields = ('id', 'job', 'job_title', 'job_company', 'candidate', 'status', 'cover_letter', 'applied_at')
        read_only_fields = ('candidate',)
