from django.db import models
from candidates.models import CandidateProfile
from jobs.models import Job
from accounts.models import User


class ResumeAnalysis(models.Model):
    candidate = models.OneToOneField(CandidateProfile, on_delete=models.CASCADE, related_name='resume_analysis')
    skills = models.JSONField(default=list)
    education = models.JSONField(default=list)
    experience = models.JSONField(default=list)
    certifications = models.JSONField(default=list)
    experience_years = models.FloatField(default=0)
    ats_score = models.FloatField(default=0)
    ats_confidence = models.FloatField(default=0)
    resume_strength = models.CharField(max_length=30, blank=True)
    missing_keywords = models.JSONField(default=list)
    weak_keywords = models.JSONField(default=list)
    recommended_keywords = models.JSONField(default=list)
    improvement_suggestions = models.JSONField(default=list)
    analyzed_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Analysis for {self.candidate.user.username}"


class JobMatch(models.Model):
    candidate = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name='job_matches')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='candidate_matches')
    match_percentage = models.FloatField(default=0)
    matching_skills = models.JSONField(default=list)
    missing_skills = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('candidate', 'job')

    def __str__(self):
        return f"{self.candidate.user.username} - {self.job.title} ({self.match_percentage}%)"


class CandidateRanking(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='rankings')
    candidate = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name='rankings')
    rank = models.PositiveIntegerField(default=0)
    match_score = models.FloatField(default=0)
    experience_score = models.FloatField(default=0)
    certification_score = models.FloatField(default=0)
    total_score = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('job', 'candidate')
        ordering = ['rank']

    def __str__(self):
        return f"Rank {self.rank}: {self.candidate.user.username} for {self.job.title}"


class AIQuestion(models.Model):
    job_title = models.CharField(max_length=200)
    skills = models.JSONField(default=list)
    experience_level = models.CharField(max_length=50)
    questions = models.JSONField(default=list)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_questions')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Questions for {self.job_title} ({self.experience_level})"


class ChatHistory(models.Model):
    candidate = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name='chat_history')
    role = models.CharField(max_length=20)  # 'user' or 'assistant'
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.candidate.user.username} - {self.role}"


class VoiceInterviewSession(models.Model):
    ROLE_CHOICES = (
        ('frontend', 'Frontend Developer'), ('backend', 'Backend Developer'),
        ('fullstack', 'Full Stack Developer'), ('java', 'Java Developer'),
        ('python', 'Python Developer'), ('hr', 'HR Interview'), ('custom', 'Custom Role'),
    )
    DIFFICULTY_CHOICES = (('beginner', 'Beginner'), ('intermediate', 'Intermediate'), ('advanced', 'Advanced'))

    candidate = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name='voice_sessions')
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default='custom')
    custom_role = models.CharField(max_length=100, blank=True)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='intermediate')
    questions = models.JSONField(default=list)
    answers = models.JSONField(default=list)
    evaluations = models.JSONField(default=list)
    overall_score = models.FloatField(default=0)
    technical_score = models.FloatField(default=0)
    communication_score = models.FloatField(default=0)
    confidence_score = models.FloatField(default=0)
    readiness_score = models.FloatField(default=0)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.candidate.user.username} - {self.role} ({self.difficulty})"


class TalentPool(models.Model):
    recruiter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='talent_pool')
    candidate = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name='talent_pool_entries')
    notes = models.TextField(blank=True)
    contacted = models.BooleanField(default=False)
    contacted_at = models.DateTimeField(null=True, blank=True)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('recruiter', 'candidate')

    def __str__(self):
        return f"{self.candidate.user.username} in {self.recruiter.username}'s pool"


class Notification(models.Model):
    EVENT_CHOICES = (
        ('new_application', 'New Application'),
        ('assessment_submission', 'Assessment Submission'),
        ('interview_scheduled', 'Interview Scheduled'),
        ('interview_completed', 'Interview Completed'),
        ('offer_sent', 'Offer Sent'),
        ('offer_accepted', 'Offer Accepted'),
        ('offer_rejected', 'Offer Rejected'),
        ('reschedule_request', 'Reschedule Request'),
        ('reschedule_approved', 'Reschedule Approved'),
        ('reschedule_rejected', 'Reschedule Rejected'),
    )

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    event = models.CharField(max_length=40, choices=EVENT_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.event} -> {self.recipient.username}"


class OfferResponse(models.Model):
    RESPONSE_CHOICES = (('accepted', 'Accepted'), ('rejected', 'Rejected'))

    decision = models.OneToOneField('interviews.CandidateDecision', on_delete=models.CASCADE, related_name='offer_response')
    response = models.CharField(max_length=10, choices=RESPONSE_CHOICES)
    remarks = models.TextField(blank=True)
    responded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.response} - {self.decision.interview.candidate.user.username}"


class ActivityLog(models.Model):
    EVENT_CHOICES = (
        ('profile_viewed', 'Profile Viewed'),
        ('job_applied', 'Job Applied'),
        ('assessment_started', 'Assessment Started'),
        ('assessment_completed', 'Assessment Completed'),
        ('interview_scheduled', 'Interview Scheduled'),
        ('interview_attended', 'Interview Attended'),
        ('offer_viewed', 'Offer Viewed'),
        ('offer_accepted', 'Offer Accepted'),
        ('offer_rejected', 'Offer Rejected'),
    )

    candidate = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name='activity_logs')
    event = models.CharField(max_length=40, choices=EVENT_CHOICES)
    description = models.TextField(blank=True)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.event} - {self.candidate.user.username}"


class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=200)
    model_name = models.CharField(max_length=100, blank=True)
    object_id = models.CharField(max_length=50, blank=True)
    changes = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} - {self.action}"
