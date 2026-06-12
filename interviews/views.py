from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from django.conf import settings

from .models import Interview, InterviewFeedback, CandidateDecision, RescheduleRequest, QuestionBank
from .serializers import (
    InterviewSerializer, InterviewFeedbackSerializer, CandidateDecisionSerializer,
    RescheduleRequestSerializer, QuestionBankSerializer,
)
from candidates.models import CandidateProfile
from .utils import generate_questions


def create_notification(recipient, event, title, message):
    try:
        from ai_features.models import Notification
        Notification.objects.create(recipient=recipient, event=event, title=title, message=message)
    except Exception:
        pass


def log_activity(candidate, event, description='', metadata=None):
    try:
        from ai_features.models import ActivityLog
        ActivityLog.objects.create(
            candidate=candidate, event=event,
            description=description, metadata=metadata or {}
        )
    except Exception:
        pass


def send_interview_email(interview):
    try:
        candidate_email = interview.candidate.user.email
        candidate_name = interview.candidate.user.username
        job_title = interview.job.title if interview.job else 'Interview'
        scheduled_at = interview.scheduled_at.strftime('%B %d, %Y at %I:%M %p')
        subject = f"Interview Scheduled: {job_title}"
        message = (
            f"Dear {candidate_name},\n\n"
            f"Your interview for '{job_title}' has been scheduled.\n\n"
            f"Date & Time: {scheduled_at}\n"
            f"Duration: {interview.duration_minutes} minutes\n"
            f"Meeting Link: {interview.meeting_link or 'Will be shared shortly'}\n\n"
            f"Notes: {interview.notes or 'N/A'}\n\n"
            f"Best regards,\nInterview Automation Portal"
        )
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [candidate_email], fail_silently=True)
    except Exception:
        pass


EMAIL_TEMPLATES = {
    'reject': {
        'subject': "Update on Your Interview — {job_title}",
        'body': (
            "Dear {candidate_name},\n\n"
            "Thank you for taking the time to interview for the {job_title} position at {company}.\n\n"
            "After careful consideration, we regret to inform you that we will not be moving forward "
            "with your application at this time.\n\n"
            "We appreciate your interest and encourage you to apply for future openings.\n\n"
            "Best regards,\n{recruiter_name}\nInterview Automation Portal"
        ),
    },
    'hold': {
        'subject': "Your Application is Under Review — {job_title}",
        'body': (
            "Dear {candidate_name},\n\n"
            "Thank you for interviewing for the {job_title} position at {company}.\n\n"
            "Your profile has been shortlisted and is currently under further consideration. "
            "We will get back to you with a final decision soon.\n\n"
            "Best regards,\n{recruiter_name}\nInterview Automation Portal"
        ),
    },
    'hire': {
        'subject': "Congratulations! Offer Letter — {job_title}",
        'body': (
            "Dear {candidate_name},\n\n"
            "Congratulations! We are thrilled to extend an offer of employment for the position of "
            "{job_title} at {company}.\n\n"
            "Position: {job_title}\nCompany: {company}\nRecruiter: {recruiter_name}\n\n"
            "Please reply to confirm your acceptance. Our HR team will follow up with onboarding details.\n\n"
            "Best regards,\n{recruiter_name}\nInterview Automation Portal"
        ),
    },
}

SUCCESS_MESSAGES = {
    'reject': 'Rejection email sent successfully.',
    'hold': 'Shortlist email sent successfully.',
    'hire': 'Offer letter sent successfully.',
}

DECISION_EVENTS = {
    'hire': ('offer_sent', 'Offer Sent', 'You have received an offer letter. Please check your email.'),
    'hold': ('offer_sent', 'Application On Hold', 'Your application has been shortlisted and is under review.'),
    'reject': ('offer_sent', 'Application Update', 'There is an update regarding your application.'),
}


class InterviewListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role == 'recruiter':
            interviews = Interview.objects.filter(recruiter=request.user).order_by('-scheduled_at')
        else:
            profile = get_object_or_404(CandidateProfile, user=request.user)
            interviews = Interview.objects.filter(candidate=profile).order_by('-scheduled_at')
        return Response(InterviewSerializer(interviews, many=True).data)

    def post(self, request):
        if request.user.role != 'recruiter':
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        serializer = InterviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        candidate_id = request.data.get('candidate')
        candidate = get_object_or_404(CandidateProfile, pk=candidate_id)
        skills = list(candidate.skills.values_list('name', flat=True))
        questions = generate_questions(skills)
        interview = serializer.save(recruiter=request.user, generated_questions=questions)
        send_interview_email(interview)
        create_notification(
            candidate.user, 'interview_scheduled',
            'Interview Scheduled',
            f"Your interview for {interview.job.title if interview.job else 'a position'} has been scheduled."
        )
        log_activity(candidate, 'interview_scheduled', f"Interview scheduled for {interview.job.title if interview.job else 'position'}")
        return Response(InterviewSerializer(interview).data, status=status.HTTP_201_CREATED)


class InterviewDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        if request.user.role == 'recruiter':
            interview = get_object_or_404(Interview, pk=pk, recruiter=request.user)
        else:
            profile = get_object_or_404(CandidateProfile, user=request.user)
            interview = get_object_or_404(Interview, pk=pk, candidate=profile)
        return Response(InterviewSerializer(interview).data)

    def patch(self, request, pk):
        interview = get_object_or_404(Interview, pk=pk, recruiter=request.user)
        serializer = InterviewSerializer(interview, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        interview = get_object_or_404(Interview, pk=pk, recruiter=request.user)
        interview.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class InterviewFeedbackView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if request.user.role != 'recruiter':
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        interview = get_object_or_404(Interview, pk=pk, recruiter=request.user)
        if hasattr(interview, 'feedback'):
            return Response({'error': 'Feedback already submitted.'}, status=status.HTTP_400_BAD_REQUEST)
        serializer = InterviewFeedbackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(interview=interview)
        interview.status = 'completed'
        interview.save()
        log_activity(interview.candidate, 'interview_attended', 'Interview completed')
        create_notification(
            interview.candidate.user, 'interview_completed',
            'Interview Completed',
            'Your interview has been marked as completed. You will hear back soon.'
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CandidateDecisionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if request.user.role != 'recruiter':
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

        interview = get_object_or_404(Interview, pk=pk, recruiter=request.user)

        if interview.status != 'completed':
            return Response({'error': 'Interview must be completed first.'}, status=status.HTTP_400_BAD_REQUEST)

        if hasattr(interview, 'decision') and interview.decision and interview.decision.delivery_status == 'sent':
            return Response(
                {'error': 'Decision email already sent.', 'decision': CandidateDecisionSerializer(interview.decision).data},
                status=status.HTTP_400_BAD_REQUEST
            )

        decision = request.data.get('decision')
        if decision not in ('reject', 'hold', 'hire'):
            return Response({'error': 'Invalid decision.'}, status=status.HTTP_400_BAD_REQUEST)

        candidate_name = interview.candidate.user.username
        candidate_email = interview.candidate.user.email
        job_title = interview.job.title if interview.job else 'the position'
        company = interview.job.company if interview.job else 'our company'
        recruiter_name = request.user.username

        template = EMAIL_TEMPLATES[decision]
        subject = template['subject'].format(job_title=job_title)
        body = template['body'].format(
            candidate_name=candidate_name, job_title=job_title,
            company=company, recruiter_name=recruiter_name,
        )

        email_sent = False
        try:
            send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [candidate_email], fail_silently=False)
            email_sent = True
        except Exception as e:
            print(f"[EMAIL ERROR] {e}")

        if hasattr(interview, 'decision') and interview.decision:
            interview.decision.delete()

        decision_obj = CandidateDecision.objects.create(
            interview=interview, decision=decision,
            sent_by=request.user,
            delivery_status='sent' if email_sent else 'failed',
        )

        # Update application status
        try:
            from jobs.models import Application
            status_map = {'hire': 'hired', 'hold': 'on_hold', 'reject': 'rejected'}
            Application.objects.filter(
                job=interview.job, candidate=interview.candidate
            ).update(status=status_map[decision])
        except Exception:
            pass

        # Notify candidate
        ev, title, msg = DECISION_EVENTS[decision]
        create_notification(interview.candidate.user, ev, title, msg)
        if decision == 'hire':
            log_activity(interview.candidate, 'offer_viewed', f"Offer letter sent for {job_title}")

        if not email_sent:
            return Response(
                {'error': 'Failed to send email. Check SMTP settings and try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response({
            'message': SUCCESS_MESSAGES[decision],
            'decision': CandidateDecisionSerializer(decision_obj).data,
        }, status=status.HTTP_201_CREATED)


class RescheduleRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        if request.user.role == 'recruiter':
            interview = get_object_or_404(Interview, pk=pk, recruiter=request.user)
        else:
            profile = get_object_or_404(CandidateProfile, user=request.user)
            interview = get_object_or_404(Interview, pk=pk, candidate=profile)
        requests_qs = interview.reschedule_requests.all().order_by('-created_at')
        return Response(RescheduleRequestSerializer(requests_qs, many=True).data)

    def post(self, request, pk):
        profile = get_object_or_404(CandidateProfile, user=request.user)
        interview = get_object_or_404(Interview, pk=pk, candidate=profile)
        if interview.reschedule_requests.filter(status='pending').exists():
            return Response({'error': 'A pending reschedule request already exists.'}, status=status.HTTP_400_BAD_REQUEST)
        serializer = RescheduleRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        rr = serializer.save(interview=interview, requested_by=request.user)
        create_notification(
            interview.recruiter, 'reschedule_request',
            'Reschedule Request',
            f"{request.user.username} has requested to reschedule the interview."
        )
        return Response(RescheduleRequestSerializer(rr).data, status=status.HTTP_201_CREATED)


class RescheduleActionView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        if request.user.role != 'recruiter':
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        rr = get_object_or_404(RescheduleRequest, pk=pk, interview__recruiter=request.user)
        action = request.data.get('action')
        if action not in ('approved', 'rejected'):
            return Response({'error': 'Invalid action.'}, status=status.HTTP_400_BAD_REQUEST)
        rr.status = action
        rr.recruiter_note = request.data.get('recruiter_note', '')
        rr.save()
        if action == 'approved':
            rr.interview.scheduled_at = rr.preferred_date
            rr.interview.status = 'rescheduled'
            rr.interview.save()
            event = 'reschedule_approved'
            title = 'Reschedule Approved'
            msg = f"Your reschedule request has been approved. New time: {rr.preferred_date.strftime('%B %d, %Y at %I:%M %p')}"
        else:
            event = 'reschedule_rejected'
            title = 'Reschedule Rejected'
            msg = f"Your reschedule request was rejected. Note: {rr.recruiter_note or 'N/A'}"
        create_notification(rr.requested_by, event, title, msg)
        try:
            send_mail(
                title,
                f"Dear {rr.requested_by.username},\n\n{msg}\n\nBest regards,\nInterview Automation Portal",
                settings.DEFAULT_FROM_EMAIL,
                [rr.requested_by.email],
                fail_silently=True,
            )
        except Exception:
            pass
        return Response(RescheduleRequestSerializer(rr).data)


class QuestionBankView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'recruiter':
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        qs = QuestionBank.objects.filter(created_by=request.user)
        category = request.query_params.get('category')
        search = request.query_params.get('search')
        if category:
            qs = qs.filter(category=category)
        if search:
            qs = qs.filter(question__icontains=search)
        return Response(QuestionBankSerializer(qs.order_by('-created_at'), many=True).data)

    def post(self, request):
        if request.user.role != 'recruiter':
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        serializer = QuestionBankSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        q = serializer.save(created_by=request.user)
        return Response(QuestionBankSerializer(q).data, status=status.HTTP_201_CREATED)


class QuestionBankDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        if request.user.role != 'recruiter':
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        q = get_object_or_404(QuestionBank, pk=pk, created_by=request.user)
        serializer = QuestionBankSerializer(q, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(QuestionBankSerializer(q).data)

    def delete(self, request, pk):
        if request.user.role != 'recruiter':
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        q = get_object_or_404(QuestionBank, pk=pk, created_by=request.user)
        q.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class GenerateQuestionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, candidate_id):
        if request.user.role != 'recruiter':
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        candidate = get_object_or_404(CandidateProfile, pk=candidate_id)
        skills = list(candidate.skills.values_list('name', flat=True))
        questions = generate_questions(skills)
        return Response({'candidate': candidate.user.username, 'skills': skills, 'questions': questions})
