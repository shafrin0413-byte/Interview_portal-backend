from django.db import models
from accounts.models import User
from candidates.models import CandidateProfile
from jobs.models import Job


class Interview(models.Model):
    STATUS_CHOICES = (
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('rescheduled', 'Rescheduled'),
    )

    recruiter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='interviews')
    candidate = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name='interviews')
    job = models.ForeignKey(Job, on_delete=models.SET_NULL, null=True, blank=True, related_name='interviews')
    scheduled_at = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(default=45)
    meeting_link = models.URLField(blank=True)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    generated_questions = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.candidate.user.username} - {self.job.title if self.job else 'Interview'} @ {self.scheduled_at}"


class InterviewFeedback(models.Model):
    interview = models.OneToOneField(Interview, on_delete=models.CASCADE, related_name='feedback')
    rating = models.PositiveIntegerField(default=0)
    remarks = models.TextField(blank=True)
    recommendation = models.CharField(max_length=20, choices=(('hire', 'Hire'), ('reject', 'Reject'), ('hold', 'Hold')), blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback for {self.interview}"


class CandidateDecision(models.Model):
    DECISION_CHOICES = (('reject', 'Reject'), ('hold', 'Hold'), ('hire', 'Hire'))
    DELIVERY_CHOICES = (('pending', 'Pending'), ('sent', 'Sent'), ('failed', 'Failed'))

    interview = models.OneToOneField(Interview, on_delete=models.CASCADE, related_name='decision')
    decision = models.CharField(max_length=10, choices=DECISION_CHOICES)
    sent_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='decisions_sent')
    sent_at = models.DateTimeField(auto_now_add=True)
    delivery_status = models.CharField(max_length=10, choices=DELIVERY_CHOICES, default='pending')

    def __str__(self):
        return f"{self.decision} — {self.interview.candidate.user.username}"


class RescheduleRequest(models.Model):
    STATUS_CHOICES = (('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected'))

    interview = models.ForeignKey(Interview, on_delete=models.CASCADE, related_name='reschedule_requests')
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE)
    preferred_date = models.DateTimeField()
    reason = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    recruiter_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Reschedule for interview {self.interview_id} - {self.status}"


class QuestionBank(models.Model):
    CATEGORY_CHOICES = (('hr', 'HR'), ('technical', 'Technical'), ('behavioral', 'Behavioral'), ('project', 'Project-Based'))

    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='question_bank')
    question = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='technical')
    tags = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.question[:80]
