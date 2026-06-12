from django.urls import path
from .views import CandidateProfileView, ResumeUploadView, ResumeDeleteView, DeleteCandidateAvatarView, SkillsView

urlpatterns = [
    path('profile/', CandidateProfileView.as_view(), name='candidate-profile'),
    path('resume/upload/', ResumeUploadView.as_view(), name='resume-upload'),
    path('resume/<int:pk>/delete/', ResumeDeleteView.as_view(), name='resume-delete'),
    path('avatar/delete/', DeleteCandidateAvatarView.as_view(), name='candidate-avatar-delete'),
    path('skills/', SkillsView.as_view(), name='skills-add'),
    path('skills/<int:pk>/', SkillsView.as_view(), name='skills-delete'),
]
