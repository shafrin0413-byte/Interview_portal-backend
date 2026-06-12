from rest_framework import serializers
from .models import Interview, InterviewFeedback, CandidateDecision, RescheduleRequest, QuestionBank


class InterviewFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewFeedback
        fields = ('id', 'rating', 'remarks', 'recommendation', 'created_at')


class CandidateDecisionSerializer(serializers.ModelSerializer):
    sent_by_name = serializers.CharField(source='sent_by.username', read_only=True)

    class Meta:
        model = CandidateDecision
        fields = ('id', 'decision', 'sent_by_name', 'sent_at', 'delivery_status')


class RescheduleRequestSerializer(serializers.ModelSerializer):
    requested_by_name = serializers.CharField(source='requested_by.username', read_only=True)

    class Meta:
        model = RescheduleRequest
        fields = ('id', 'interview', 'requested_by_name', 'preferred_date', 'reason', 'status', 'recruiter_note', 'created_at', 'updated_at')
        read_only_fields = ('interview', 'status', 'recruiter_note', 'requested_by_name')


class QuestionBankSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionBank
        fields = ('id', 'question', 'category', 'tags', 'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at')


class InterviewSerializer(serializers.ModelSerializer):
    candidate_name = serializers.CharField(source='candidate.user.username', read_only=True)
    candidate_email = serializers.CharField(source='candidate.user.email', read_only=True)
    recruiter_name = serializers.CharField(source='recruiter.username', read_only=True)
    job_title = serializers.CharField(source='job.title', read_only=True, allow_null=True)
    feedback = InterviewFeedbackSerializer(read_only=True)
    decision = serializers.SerializerMethodField()
    reschedule_requests = RescheduleRequestSerializer(many=True, read_only=True)

    class Meta:
        model = Interview
        fields = (
            'id', 'recruiter_name', 'candidate_name', 'candidate_email',
            'job_title', 'job', 'candidate', 'scheduled_at', 'duration_minutes',
            'meeting_link', 'notes', 'status', 'generated_questions',
            'feedback', 'decision', 'reschedule_requests', 'created_at'
        )
        read_only_fields = ('recruiter', 'generated_questions')

    def get_decision(self, obj):
        try:
            if hasattr(obj, 'decision') and obj.decision:
                return CandidateDecisionSerializer(obj.decision).data
        except Exception:
            pass
        return None
