from django.urls import path
from .views import (
    JobListCreateView, JobDetailView, ApplyJobView,
    JobApplicationsView, ApplicationStatusView,
    CandidateApplicationsView, RecruiterStatsView,
    RecruiterAnalyticsView, CandidateAnalyticsView
)

urlpatterns = [
    path('', JobListCreateView.as_view(), name='job-list-create'),
    path('<int:pk>/', JobDetailView.as_view(), name='job-detail'),
    path('<int:pk>/apply/', ApplyJobView.as_view(), name='job-apply'),
    path('<int:pk>/applications/', JobApplicationsView.as_view(), name='job-applications'),
    path('applications/<int:pk>/status/', ApplicationStatusView.as_view(), name='application-status'),
    path('my-applications/', CandidateApplicationsView.as_view(), name='my-applications'),
    path('recruiter/stats/', RecruiterStatsView.as_view(), name='recruiter-stats'),
    path('recruiter/analytics/', RecruiterAnalyticsView.as_view(), name='recruiter-analytics'),
    path('candidate/analytics/', CandidateAnalyticsView.as_view(), name='candidate-analytics'),
]
