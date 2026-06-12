from django.urls import path
from .views import (
    InterviewListCreateView, InterviewDetailView,
    InterviewFeedbackView, GenerateQuestionsView,
    CandidateDecisionView, RescheduleRequestView,
    RescheduleActionView, QuestionBankView, QuestionBankDetailView,
)

urlpatterns = [
    path('', InterviewListCreateView.as_view(), name='interview-list-create'),
    path('<int:pk>/', InterviewDetailView.as_view(), name='interview-detail'),
    path('<int:pk>/feedback/', InterviewFeedbackView.as_view(), name='interview-feedback'),
    path('<int:pk>/decision/', CandidateDecisionView.as_view(), name='candidate-decision'),
    path('<int:pk>/reschedule/', RescheduleRequestView.as_view(), name='reschedule-request'),
    path('reschedule/<int:pk>/action/', RescheduleActionView.as_view(), name='reschedule-action'),
    path('generate-questions/<int:candidate_id>/', GenerateQuestionsView.as_view(), name='generate-questions'),
    path('question-bank/', QuestionBankView.as_view(), name='question-bank'),
    path('question-bank/<int:pk>/', QuestionBankDetailView.as_view(), name='question-bank-detail'),
]
