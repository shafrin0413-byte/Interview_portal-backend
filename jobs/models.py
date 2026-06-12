from django.db import models
from django.utils import timezone
from accounts.models import User
from candidates.models import CandidateProfile


class Job(models.Model):
    STATUS_CHOICES = (('open', 'Open'), ('closed', 'Closed'), ('draft', 'Draft'), ('expired', 'Expired'))
    JOB_TYPE_CHOICES = (('full-time', 'Full-Time'), ('part-time', 'Part-Time'), ('contract', 'Contract'), ('internship', 'Internship'))
    WORK_MODE_CHOICES = (('on-site', 'On-Site'), ('remote', 'Remote'), ('hybrid', 'Hybrid'))
    EXPERIENCE_CHOICES = (('fresher', 'Fresher'), ('1-2', '1-2 Years'), ('3-5', '3-5 Years'), ('5+', '5+ Years'))

    recruiter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='jobs')
    title = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    location = models.CharField(max_length=200, blank=True)
    work_mode = models.CharField(max_length=20, choices=WORK_MODE_CHOICES, default='on-site')
    job_type = models.CharField(max_length=20, choices=JOB_TYPE_CHOICES, default='full-time')
    experience = models.CharField(max_length=20, choices=EXPERIENCE_CHOICES, default='fresher')
    salary = models.CharField(max_length=100, blank=True)
    description = models.TextField()
    requirements = models.TextField(blank=True)
    skills_required = models.CharField(max_length=500, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='open')
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_expired(self):
        return self.expires_at and timezone.now() > self.expires_at

    def __str__(self):
        return f"{self.title} at {self.company}"


class Application(models.Model):
    STATUS_CHOICES = (
        ('applied', 'Applied'),
        ('shortlisted', 'Shortlisted'),
        ('rejected', 'Rejected'),
        ('interview', 'Interview Scheduled'),
        ('hired', 'Hired'),
        ('on_hold', 'On Hold'),
    )

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    candidate = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name='applications')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='applied')
    cover_letter = models.TextField(blank=True)
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('job', 'candidate')

    def __str__(self):
        return f"{self.candidate.user.username} → {self.job.title}"
