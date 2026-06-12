from rest_framework import serializers
from .models import (
    ResumeAnalysis, JobMatch, CandidateRanking, AIQuestion,
    ChatHistory, VoiceInterviewSession, TalentPool,
    Notification, OfferResponse, ActivityLog, AuditLog,
)


class ResumeAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResumeAnalysis
        fields = '__all__'
        read_only_fields = ('candidate',)


class JobMatchSerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(source='job.title', read_only=True)

    class Meta:
        model = JobMatch
        fields = ('id', 'job', 'job_title', 'match_percentage', 'matching_skills', 'missing_skills', 'created_at')


class CandidateRankingSerializer(serializers.ModelSerializer):
    candidate_name = serializers.CharField(source='candidate.user.username', read_only=True)
    candidate_email = serializers.CharField(source='candidate.user.email', read_only=True)
    candidate_id = serializers.IntegerField(source='candidate.id', read_only=True)

    class Meta:
        model = CandidateRanking
        fields = ('id', 'rank', 'candidate_id', 'candidate_name', 'candidate_email', 'match_score', 'experience_score', 'certification_score', 'total_score')


class AIQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIQuestion
        fields = ('id', 'job_title', 'skills', 'experience_level', 'questions', 'created_at')
        read_only_fields = ('created_at',)


class ChatHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatHistory
        fields = ('id', 'role', 'content', 'created_at')


class VoiceInterviewSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = VoiceInterviewSession
        fields = '__all__'
        read_only_fields = ('candidate', 'completed', 'completed_at')


class TalentPoolSerializer(serializers.ModelSerializer):
    candidate_name = serializers.CharField(source='candidate.user.username', read_only=True)
    candidate_email = serializers.CharField(source='candidate.user.email', read_only=True)
    candidate_id = serializers.IntegerField(source='candidate.id', read_only=True)
    skills = serializers.SerializerMethodField()
    ats_score = serializers.SerializerMethodField()
    experience_years = serializers.SerializerMethodField()

    class Meta:
        model = TalentPool
        fields = ('id', 'candidate_id', 'candidate_name', 'candidate_email', 'skills', 'ats_score', 'experience_years', 'notes', 'contacted', 'contacted_at', 'added_at')
        read_only_fields = ('added_at',)

    def get_skills(self, obj):
        return list(obj.candidate.skills.values_list('name', flat=True))

    def get_ats_score(self, obj):
        try:
            return obj.candidate.resume_analysis.ats_score
        except Exception:
            return 0

    def get_experience_years(self, obj):
        try:
            return obj.candidate.resume_analysis.experience_years
        except Exception:
            return 0


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ('id', 'event', 'title', 'message', 'is_read', 'created_at')


class OfferResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = OfferResponse
        fields = ('id', 'response', 'remarks', 'responded_at')
        read_only_fields = ('responded_at',)


class ActivityLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityLog
        fields = ('id', 'event', 'description', 'metadata', 'created_at')


class AuditLogSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = AuditLog
        fields = ('id', 'user_name', 'action', 'model_name', 'object_id', 'changes', 'ip_address', 'created_at')
