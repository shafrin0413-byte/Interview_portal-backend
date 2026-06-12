from django.db import models
from accounts.models import User


class Certification(models.Model):
    candidate = models.ForeignKey('CandidateProfile', on_delete=models.CASCADE, related_name='certifications')
    name = models.CharField(max_length=200)
    issuer = models.CharField(max_length=200, blank=True)
    year = models.CharField(max_length=10, blank=True)

    def __str__(self):
        return self.name


class CandidateProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='candidate_profile')
    headline = models.CharField(max_length=200, blank=True)
    bio = models.TextField(blank=True)
    location = models.CharField(max_length=100, blank=True)
    linkedin = models.URLField(blank=True)
    github = models.URLField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s profile"


class Resume(models.Model):
    candidate = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name='resumes')
    file = models.FileField(upload_to='resumes/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.candidate.user.username} - resume"


class Skill(models.Model):
    candidate = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name='skills')
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Education(models.Model):
    candidate = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name='education')
    degree = models.CharField(max_length=200)
    institution = models.CharField(max_length=200)
    year = models.CharField(max_length=10, blank=True)

    def __str__(self):
        return f"{self.degree} - {self.institution}"


class Experience(models.Model):
    candidate = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name='experience')
    title = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    duration = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.title} at {self.company}"
