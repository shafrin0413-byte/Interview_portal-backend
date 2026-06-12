from django.db import models
from accounts.models import User
from candidates.models import CandidateProfile


class Assessment(models.Model):
    recruiter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assessments')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    duration_minutes = models.PositiveIntegerField(default=30)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Question(models.Model):
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    option_a = models.CharField(max_length=300)
    option_b = models.CharField(max_length=300)
    option_c = models.CharField(max_length=300)
    option_d = models.CharField(max_length=300)
    correct_option = models.CharField(max_length=1, choices=[('A','A'),('B','B'),('C','C'),('D','D')])
    marks = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"Q: {self.text[:60]}"


class AssessmentAssignment(models.Model):
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='assignments')
    candidate = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name='assignments')
    assigned_at = models.DateTimeField(auto_now_add=True)
    is_completed = models.BooleanField(default=False)

    class Meta:
        unique_together = ('assessment', 'candidate')

    def __str__(self):
        return f"{self.candidate.user.username} → {self.assessment.title}"


class AssessmentResult(models.Model):
    assignment = models.OneToOneField(AssessmentAssignment, on_delete=models.CASCADE, related_name='result')
    score = models.PositiveIntegerField(default=0)
    total_marks = models.PositiveIntegerField(default=0)
    percentage = models.FloatField(default=0.0)
    answers = models.JSONField(default=dict)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.assignment.candidate.user.username} - {self.score}/{self.total_marks}"
