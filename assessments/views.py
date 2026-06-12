from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from .models import Assessment, Question, AssessmentAssignment, AssessmentResult
from .serializers import (
    AssessmentSerializer, QuestionSerializer,
    AssessmentAssignmentSerializer, QuestionCandidateSerializer
)
from candidates.models import CandidateProfile


class AssessmentListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'recruiter':
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        assessments = Assessment.objects.filter(recruiter=request.user).order_by('-created_at')
        return Response(AssessmentSerializer(assessments, many=True).data)

    def post(self, request):
        if request.user.role != 'recruiter':
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        serializer = AssessmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(recruiter=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AssessmentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        assessment = get_object_or_404(Assessment, pk=pk, recruiter=request.user)
        return Response(AssessmentSerializer(assessment).data)

    def patch(self, request, pk):
        assessment = get_object_or_404(Assessment, pk=pk, recruiter=request.user)
        serializer = AssessmentSerializer(assessment, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        assessment = get_object_or_404(Assessment, pk=pk, recruiter=request.user)
        assessment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class QuestionCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        assessment = get_object_or_404(Assessment, pk=pk, recruiter=request.user)
        serializer = QuestionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(assessment=assessment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, pk, qpk):
        question = get_object_or_404(Question, pk=qpk, assessment__recruiter=request.user)
        question.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AssignAssessmentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if request.user.role != 'recruiter':
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        assessment = get_object_or_404(Assessment, pk=pk, recruiter=request.user)
        candidate_id = request.data.get('candidate_id')
        candidate = get_object_or_404(CandidateProfile, pk=candidate_id)
        assignment, created = AssessmentAssignment.objects.get_or_create(
            assessment=assessment, candidate=candidate
        )
        if not created:
            return Response({'error': 'Already assigned.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(AssessmentAssignmentSerializer(assignment).data, status=status.HTTP_201_CREATED)

    def get(self, request, pk):
        """List all assignments for an assessment"""
        assessment = get_object_or_404(Assessment, pk=pk, recruiter=request.user)
        assignments = assessment.assignments.all()
        return Response(AssessmentAssignmentSerializer(assignments, many=True).data)


class CandidateAssignmentsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = get_object_or_404(CandidateProfile, user=request.user)
        assignments = profile.assignments.select_related('assessment', 'result').all()
        return Response(AssessmentAssignmentSerializer(assignments, many=True).data)


class TakeAssessmentView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """Get assessment questions (without answers) for candidate"""
        profile = get_object_or_404(CandidateProfile, user=request.user)
        assignment = get_object_or_404(AssessmentAssignment, pk=pk, candidate=profile, is_completed=False)
        questions = QuestionCandidateSerializer(assignment.assessment.questions.all(), many=True).data
        return Response({
            'assignment_id': assignment.id,
            'title': assignment.assessment.title,
            'description': assignment.assessment.description,
            'duration_minutes': assignment.assessment.duration_minutes,
            'questions': questions
        })

    def post(self, request, pk):
        """Submit answers and auto-calculate score"""
        profile = get_object_or_404(CandidateProfile, user=request.user)
        assignment = get_object_or_404(AssessmentAssignment, pk=pk, candidate=profile, is_completed=False)

        answers = request.data.get('answers', {})  # {question_id: selected_option}
        questions = assignment.assessment.questions.all()
        score = 0
        total = sum(q.marks for q in questions)

        for question in questions:
            submitted = answers.get(str(question.id), '').upper()
            if submitted == question.correct_option:
                score += question.marks

        percentage = round((score / total) * 100, 2) if total > 0 else 0

        AssessmentResult.objects.create(
            assignment=assignment,
            score=score,
            total_marks=total,
            percentage=percentage,
            answers=answers
        )
        assignment.is_completed = True
        assignment.save()

        return Response({'score': score, 'total_marks': total, 'percentage': percentage})
