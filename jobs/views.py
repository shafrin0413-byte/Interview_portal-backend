from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Count

from .models import Job, Application
from .serializers import JobSerializer, ApplicationSerializer
from candidates.models import CandidateProfile


class JobListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django.utils import timezone
        if request.user.role == 'recruiter':
            jobs = Job.objects.filter(recruiter=request.user).order_by('-created_at')
        else:
            # Auto-expire jobs before listing
            Job.objects.filter(status='open', expires_at__lt=timezone.now()).update(status='expired')
            jobs = Job.objects.filter(status__in=['open', 'expired']).order_by('-created_at')
        return Response(JobSerializer(jobs, many=True).data)

    def post(self, request):
        if request.user.role != 'recruiter':
            return Response({'error': 'Only recruiters can post jobs.'}, status=status.HTTP_403_FORBIDDEN)
        serializer = JobSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(recruiter=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class JobDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        job = get_object_or_404(Job, pk=pk)
        return Response(JobSerializer(job).data)

    def patch(self, request, pk):
        job = get_object_or_404(Job, pk=pk, recruiter=request.user)
        serializer = JobSerializer(job, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        job = get_object_or_404(Job, pk=pk, recruiter=request.user)
        job.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ApplyJobView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if request.user.role != 'candidate':
            return Response({'error': 'Only candidates can apply.'}, status=status.HTTP_403_FORBIDDEN)
        job = get_object_or_404(Job, pk=pk)
        # Auto-expire check
        from django.utils import timezone
        if job.is_expired() and job.status == 'open':
            job.status = 'expired'
            job.save()
        if job.status not in ('open',):
            return Response({'error': 'This job is not accepting applications.'}, status=status.HTTP_400_BAD_REQUEST)
        profile, _ = CandidateProfile.objects.get_or_create(user=request.user)
        if Application.objects.filter(job=job, candidate=profile).exists():
            return Response({'error': 'You have already applied to this job.'}, status=status.HTTP_400_BAD_REQUEST)
        application = Application.objects.create(
            job=job, candidate=profile,
            cover_letter=request.data.get('cover_letter', '')
        )
        try:
            from ai_features.models import Notification, ActivityLog
            Notification.objects.create(
                recipient=job.recruiter, event='new_application',
                title='New Application',
                message=f"{request.user.username} applied for {job.title}."
            )
            ActivityLog.objects.create(candidate=profile, event='job_applied', description=f"Applied for {job.title}")
        except Exception:
            pass
        return Response(ApplicationSerializer(application).data, status=status.HTTP_201_CREATED)


class JobApplicationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        job = get_object_or_404(Job, pk=pk, recruiter=request.user)
        applications = job.applications.all().order_by('-applied_at')
        return Response(ApplicationSerializer(applications, many=True).data)


class ApplicationStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        application = get_object_or_404(Application, pk=pk, job__recruiter=request.user)
        new_status = request.data.get('status')
        if new_status not in dict(Application.STATUS_CHOICES):
            return Response({'error': 'Invalid status.'}, status=status.HTTP_400_BAD_REQUEST)
        application.status = new_status
        application.save()
        return Response(ApplicationSerializer(application).data)


class CandidateApplicationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile, _ = CandidateProfile.objects.get_or_create(user=request.user)
        applications = profile.applications.all().order_by('-applied_at')
        return Response(ApplicationSerializer(applications, many=True).data)


class RecruiterStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'recruiter':
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        jobs = Job.objects.filter(recruiter=request.user)
        total_jobs = jobs.count()
        open_jobs = jobs.filter(status='open').count()
        total_applications = Application.objects.filter(job__recruiter=request.user).count()
        shortlisted = Application.objects.filter(job__recruiter=request.user, status='shortlisted').count()
        return Response({
            'total_jobs': total_jobs,
            'open_jobs': open_jobs,
            'total_applications': total_applications,
            'shortlisted': shortlisted,
        })


class RecruiterAnalyticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'recruiter':
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

        jobs = Job.objects.filter(recruiter=request.user)

        # Applications per job
        apps_per_job = [
            {'job': j.title, 'count': j.applications.count()}
            for j in jobs
        ]

        # Application status breakdown
        status_counts = (
            Application.objects
            .filter(job__recruiter=request.user)
            .values('status')
            .annotate(count=Count('id'))
        )
        status_breakdown = {s['status']: s['count'] for s in status_counts}

        # Interview status breakdown
        try:
            from interviews.models import Interview
            interview_statuses = (
                Interview.objects
                .filter(recruiter=request.user)
                .values('status')
                .annotate(count=Count('id'))
            )
            interview_breakdown = {s['status']: s['count'] for s in interview_statuses}
        except Exception:
            interview_breakdown = {}

        # Jobs by status
        job_status = {
            'open': jobs.filter(status='open').count(),
            'closed': jobs.filter(status='closed').count(),
            'draft': jobs.filter(status='draft').count(),
        }

        # Top skills demanded across jobs
        skill_demand = {}
        for job in jobs:
            for skill in [s.strip().lower() for s in job.skills_required.split(',') if s.strip()]:
                skill_demand[skill] = skill_demand.get(skill, 0) + 1
        top_skills = sorted(skill_demand.items(), key=lambda x: x[1], reverse=True)[:8]

        return Response({
            'apps_per_job': apps_per_job,
            'status_breakdown': status_breakdown,
            'interview_breakdown': interview_breakdown,
            'job_status': job_status,
            'top_skills_demanded': [{'skill': k, 'count': v} for k, v in top_skills],
        })


class CandidateAnalyticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'candidate':
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

        profile, _ = CandidateProfile.objects.get_or_create(user=request.user)
        applications = profile.applications.all()

        # Application status breakdown
        status_counts = applications.values('status').annotate(count=Count('id'))
        status_breakdown = {s['status']: s['count'] for s in status_counts}

        # Total counts
        total_apps = applications.count()
        shortlisted = applications.filter(status='shortlisted').count()
        interviews = applications.filter(status='interview').count()
        rejected = applications.filter(status='rejected').count()

        # Skills count
        skills = list(profile.skills.values_list('name', flat=True))

        # Job matches
        from ai_features.models import JobMatch
        matches = JobMatch.objects.filter(candidate=profile).order_by('-match_percentage')[:5]
        top_matches = [{
            'job_title': m.job.title,
            'match_percentage': m.match_percentage,
            'matching_skills': m.matching_skills,
            'missing_skills': m.missing_skills,
        } for m in matches]

        # Interview stats
        from interviews.models import Interview
        my_interviews = Interview.objects.filter(candidate=profile)
        interview_status = my_interviews.values('status').annotate(count=Count('id'))
        interview_breakdown = {s['status']: s['count'] for s in interview_status}

        # Latest decision
        try:
            from interviews.models import CandidateDecision
            latest_decision = CandidateDecision.objects.filter(
                interview__candidate=profile
            ).order_by('-sent_at').first()
            decision_status = latest_decision.decision if latest_decision else None
        except Exception:
            decision_status = None

        return Response({
            'total_applications': total_apps,
            'shortlisted': shortlisted,
            'interviews_scheduled': interviews,
            'rejected': rejected,
            'status_breakdown': status_breakdown,
            'skills': skills,
            'top_job_matches': top_matches,
            'interview_breakdown': interview_breakdown,
            'latest_decision': decision_status,
        })
