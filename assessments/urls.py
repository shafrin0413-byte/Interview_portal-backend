from django.urls import path
from .views import (
    AssessmentListCreateView, AssessmentDetailView,
    QuestionCreateView, AssignAssessmentView,
    CandidateAssignmentsView, TakeAssessmentView
)

urlpatterns = [
    path('', AssessmentListCreateView.as_view(), name='assessment-list-create'),
    path('<int:pk>/', AssessmentDetailView.as_view(), name='assessment-detail'),
    path('<int:pk>/questions/', QuestionCreateView.as_view(), name='question-create'),
    path('<int:pk>/questions/<int:qpk>/', QuestionCreateView.as_view(), name='question-delete'),
    path('<int:pk>/assign/', AssignAssessmentView.as_view(), name='assign-assessment'),
    path('my-assignments/', CandidateAssignmentsView.as_view(), name='my-assignments'),
    path('take/<int:pk>/', TakeAssessmentView.as_view(), name='take-assessment'),
]
