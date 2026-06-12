from rest_framework import serializers
from .models import Assessment, Question, AssessmentAssignment, AssessmentResult


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ('id', 'text', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_option', 'marks')


class QuestionCandidateSerializer(serializers.ModelSerializer):
    """Hides correct answer from candidates"""
    class Meta:
        model = Question
        fields = ('id', 'text', 'option_a', 'option_b', 'option_c', 'option_d', 'marks')


class AssessmentSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)
    question_count = serializers.SerializerMethodField()

    class Meta:
        model = Assessment
        fields = ('id', 'title', 'description', 'duration_minutes', 'question_count', 'questions', 'created_at')
        read_only_fields = ('recruiter',)

    def get_question_count(self, obj):
        return obj.questions.count()


class AssessmentResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssessmentResult
        fields = ('id', 'score', 'total_marks', 'percentage', 'submitted_at')


class AssessmentAssignmentSerializer(serializers.ModelSerializer):
    assessment = AssessmentSerializer(read_only=True)
    result = AssessmentResultSerializer(read_only=True)
    candidate_name = serializers.CharField(source='candidate.user.username', read_only=True)

    class Meta:
        model = AssessmentAssignment
        fields = ('id', 'assessment', 'candidate_name', 'is_completed', 'assigned_at', 'result')
