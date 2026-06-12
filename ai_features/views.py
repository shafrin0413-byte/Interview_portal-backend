from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.utils import timezone
import csv
import io
import json

from .models import (
    ResumeAnalysis, JobMatch, CandidateRanking, AIQuestion,
    ChatHistory, VoiceInterviewSession, TalentPool,
    Notification, OfferResponse, ActivityLog, AuditLog,
)
from .serializers import (
    ResumeAnalysisSerializer, JobMatchSerializer, CandidateRankingSerializer,
    AIQuestionSerializer, ChatHistorySerializer, VoiceInterviewSessionSerializer,
    TalentPoolSerializer, NotificationSerializer, OfferResponseSerializer,
    ActivityLogSerializer, AuditLogSerializer,
)
from .services import calculate_job_match, rank_candidates_for_job, sync_resume_analysis, generate_ai_questions
from candidates.models import CandidateProfile
from jobs.models import Job, Application


def get_openai_client():
    try:
        from openai import OpenAI
        return OpenAI(api_key=settings.OPENAI_API_KEY)
    except Exception:
        return None


import random
import re
from collections import Counter


def local_ai_recruiter_chat(message):
    """Local AI chat for recruiters"""
    msg = message.lower()

    if any(w in msg for w in ['job description', 'jd', 'job post', 'write a job']):
        return random.choice([
            "For a great job description: 1) Start with a compelling company overview 2) List clear responsibilities 3) Separate 'Required' vs 'Nice-to-have' skills 4) Include salary range 5) Highlight culture and benefits. Specific, honest JDs attract better candidates.",
            "Job description tips: Use inclusive language, quantify team size and impact, list 5-7 must-have skills (not 20+), mention tech stack clearly, and always include growth opportunities. Avoid internal jargon.",
        ])

    elif any(w in msg for w in ['interview', 'question', 'assess', 'evaluate']):
        return random.choice([
            "Effective interview strategies: 1) Use structured interviews for fairness 2) Include technical, behavioral, and situational questions 3) Score each answer consistently 4) Have multiple interviewers 5) Allow candidates to ask questions. STAR-based questions reveal real competencies.",
            "Great interview questions uncover problem-solving, collaboration, and growth mindset. Avoid yes/no questions. Ask 'Tell me about a time when...' and 'How would you approach...' to get deeper insights into candidate thinking.",
        ])

    elif any(w in msg for w in ['hire', 'hiring', 'recruit', 'talent', 'candidate']):
        return random.choice([
            "Hiring best practices: Define the role clearly before posting, use multiple sourcing channels, screen resumes for relevant skills, conduct structured interviews, check references, and move quickly — top candidates are off the market within 10 days.",
            "To improve your hiring pipeline: 1) Write clear job descriptions 2) Source from LinkedIn, job boards, and referrals 3) Use skills-based screening 4) Provide timely feedback 5) Create a positive candidate experience — even rejected candidates can become future hires or company advocates.",
        ])

    elif any(w in msg for w in ['onboard', 'offer', 'salary', 'compensation']):
        return random.choice([
            "Offer and onboarding tips: Research market salaries before making offers, move quickly after decisions, provide a clear onboarding plan for day 1, assign a buddy or mentor, and check in at 30/60/90 days. A great first week reduces early turnover significantly.",
            "Compensation strategy: Use market data (Glassdoor, LinkedIn Salary), consider total compensation (salary + benefits + growth), be transparent about ranges in job postings, and ensure internal pay equity. Candidates appreciate honesty over negotiation games.",
        ])

    elif any(w in msg for w in ['skill', 'tech', 'technical', 'stack', 'require']):
        return random.choice([
            "Skill assessment tips: Focus on must-have vs nice-to-have skills, use practical coding tests or take-home projects for technical roles, assess problem-solving over memorized answers, and consider learning potential alongside current skills.",
            "When defining required skills: Talk to the hiring manager about what the person will actually do in week 1, identify the 3-5 truly non-negotiable skills, and be open to candidates from adjacent backgrounds who can learn quickly.",
        ])

    else:
        return random.choice([
            "I'm your AI Recruiter Assistant! I can help you with: ✓ Writing job descriptions ✓ Creating interview questions ✓ Candidate evaluation ✓ Hiring strategies ✓ Onboarding tips. What would you like help with?",
            "As your AI hiring assistant, I can help craft job descriptions, generate interview questions, evaluate candidate responses, and suggest best practices for building a strong team. What's on your mind?",
        ])


def local_ai_chat(messages, context='general'):
    """Local AI chat without OpenAI API key"""
    user_message = messages[-1]['content'].lower() if messages else ''
    
    # Resume & Career Help
    if any(word in user_message for word in ['resume', 'cv', 'profile']):
        return random.choice([
            "To improve your resume: 1) Use action verbs like 'developed', 'implemented', 'optimized' 2) Quantify achievements with numbers 3) Tailor skills to job requirements 4) Keep it concise (1-2 pages) 5) Include relevant projects and certifications.",
            "Key resume tips: Start with a strong professional summary, highlight your top 3-5 technical skills, showcase measurable accomplishments, and ensure ATS compatibility by using standard formatting and keywords from job descriptions.",
            "For a standout resume: Focus on results over responsibilities, use consistent formatting, include a skills section with both technical and soft skills, add links to your portfolio/GitHub, and proofread thoroughly."
        ])
    
    # Interview Preparation
    elif any(word in user_message for word in ['interview', 'questions', 'prepare']):
        return random.choice([
            "Interview preparation essentials: 1) Research the company and role 2) Practice STAR method for behavioral questions 3) Prepare technical examples 4) Ask thoughtful questions 5) Practice coding problems if technical role 6) Plan your outfit and route.",
            "Common interview topics to prepare: Tell me about yourself, your biggest strength/weakness, why you want this role, describe a challenging project, how you handle conflicts, and your career goals.",
            "Technical interview tips: Explain your thought process aloud, ask clarifying questions, start with a simple solution then optimize, test your code, and discuss trade-offs between different approaches."
        ])
    
    # Skills & Learning
    elif any(word in user_message for word in ['skills', 'learn', 'technology', 'programming']):
        return random.choice([
            "In-demand tech skills for 2024: Cloud platforms (AWS/Azure), JavaScript/Python, React/Node.js, Docker/Kubernetes, AI/ML basics, cybersecurity, data analysis, and mobile development. Focus on 2-3 areas deeply rather than many superficially.",
            "Learning strategy: Pick projects that combine multiple skills, contribute to open source, build a portfolio, get certifications, join tech communities, and practice consistently. Hands-on experience beats theoretical knowledge.",
            "Skill development path: Start with fundamentals, build projects, get feedback, learn from failures, stay updated with industry trends, and network with professionals. Document your learning journey."
        ])
    
    # Career Growth
    elif any(word in user_message for word in ['career', 'growth', 'promotion', 'salary']):
        return random.choice([
            "Career advancement tips: Set clear goals, seek mentorship, take on challenging projects, develop leadership skills, build your network, document achievements, ask for feedback, and communicate your value to managers.",
            "For career growth: Become a go-to person in your area, help others succeed, stay curious and keep learning, build cross-functional relationships, and don't be afraid to take calculated risks.",
            "Salary negotiation: Research market rates, document your contributions, time it right (performance reviews/job offers), practice your pitch, consider total compensation, and be prepared to walk away if needed."
        ])
    
    # Job Search
    elif any(word in user_message for word in ['job', 'apply', 'search', 'opportunity']):
        return random.choice([
            "Job search strategy: Optimize your LinkedIn profile, network actively, apply to quality positions that match your skills, customize applications, follow up professionally, and consider referrals from your network.",
            "Effective job hunting: Use multiple platforms (LinkedIn, company websites, job boards), set up job alerts, track applications, prepare a 30-second elevator pitch, and maintain a positive attitude throughout the process.",
            "Application tips: Tailor your resume for each role, write compelling cover letters, apply within the first few days of posting, research the company culture, and prepare for different interview formats."
        ])
    
    # General Support
    else:
        return random.choice([
            "I'm here to help with your career development! I can assist with resume optimization, interview preparation, skill development, job search strategies, and career planning. What specific area would you like to focus on?",
            "As your AI career assistant, I can help you with: ✓ Resume and profile improvement ✓ Interview preparation ✓ Skill gap analysis ✓ Career roadmap planning ✓ Job search strategies. What's your biggest career challenge right now?",
            "Let's work on advancing your career! I can provide guidance on technical skills development, networking strategies, interview techniques, resume optimization, and career growth planning. What would you like to explore?"
        ])


def analyze_resume_content(skills_text, experience_text, education_text):
    """Analyze resume content without OpenAI"""
    score = 0
    feedback = []
    
    # Skills analysis
    skills_count = len([s.strip() for s in skills_text.split(',') if s.strip()]) if skills_text else 0
    if skills_count >= 5:
        score += 25
        feedback.append("✓ Good variety of skills listed")
    else:
        feedback.append("• Add more relevant technical skills")
    
    # Experience analysis
    if experience_text and len(experience_text) > 100:
        score += 25
        if any(word in experience_text.lower() for word in ['developed', 'implemented', 'created', 'managed', 'led']):
            score += 10
            feedback.append("✓ Uses strong action verbs")
        if re.search(r'\d+', experience_text):
            score += 10
            feedback.append("✓ Includes quantified achievements")
    else:
        feedback.append("• Expand experience descriptions with specific achievements")
    
    # Education analysis
    if education_text:
        score += 15
        feedback.append("✓ Education section completed")
    
    return min(score, 100), feedback


def generate_job_questions(job_title, skills, experience_level):
    """Generate interview questions without OpenAI"""
    question_banks = {
        'technical': {
            'python': ['Explain Python decorators', 'What is GIL?', 'Difference between list and tuple'],
            'javascript': ['Explain closures', 'What is event loop?', 'Difference between let and var'],
            'react': ['What are React hooks?', 'Explain virtual DOM', 'Lifecycle methods vs useEffect'],
            'java': ['Explain OOP concepts', 'What is JVM?', 'Collections framework'],
            'default': ['Describe your coding approach', 'How do you debug issues?', 'Explain a complex project']
        },
        'behavioral': [
            'Tell me about a challenging project',
            'How do you handle tight deadlines?',
            'Describe a time you disagreed with a team member',
            'What motivates you professionally?',
            'How do you stay updated with technology?'
        ],
        'hr': [
            'Tell me about yourself',
            'Why are you interested in this role?',
            'Where do you see yourself in 5 years?',
            'What is your greatest strength?',
            'Why should we hire you?'
        ]
    }
    
    questions = []
    
    # Add HR questions
    questions.extend(random.sample(question_banks['hr'], 2))
    
    # Add behavioral questions
    questions.extend(random.sample(question_banks['behavioral'], 2))
    
    # Add technical questions based on skills
    tech_questions = []
    for skill in skills[:3]:  # Top 3 skills
        skill_lower = skill.lower()
        if skill_lower in question_banks['technical']:
            tech_questions.extend(question_banks['technical'][skill_lower])
    
    if not tech_questions:
        tech_questions = question_banks['technical']['default']
    
    questions.extend(random.sample(tech_questions, min(3, len(tech_questions))))
    
    # Adjust difficulty based on experience level
    if experience_level == 'senior':
        questions.extend([
            'How do you mentor junior developers?',
            'Describe your approach to system architecture',
            'How do you handle technical debt?'
        ])
    
    return questions[:8]  # Return 8 questions


def calculate_skill_match(candidate_skills, job_skills):
    """Calculate job match percentage"""
    if not candidate_skills or not job_skills:
        return 0, [], []
    
    candidate_set = set(s.lower().strip() for s in candidate_skills)
    job_set = set(s.lower().strip() for s in job_skills if s.strip())
    
    matching = candidate_set & job_set
    missing = job_set - candidate_set
    
    match_percentage = round((len(matching) / len(job_set)) * 100) if job_set else 0
    
    return match_percentage, list(matching), list(missing)


def generate_career_guidance(skills_list):
    """Generate career guidance based on skills"""
    skill_categories = {
        'frontend': ['react', 'javascript', 'html', 'css', 'vue', 'angular'],
        'backend': ['python', 'java', 'node', 'django', 'spring', 'api'],
        'data': ['python', 'sql', 'pandas', 'numpy', 'machine learning', 'ai'],
        'cloud': ['aws', 'azure', 'docker', 'kubernetes', 'devops'],
        'mobile': ['react native', 'flutter', 'ios', 'android', 'swift']
    }
    
    user_categories = []
    for category, category_skills in skill_categories.items():
        if any(skill.lower() in [s.lower() for s in skills_list] for skill in category_skills):
            user_categories.append(category)
    
    guidance = {
        'recommended_skills': [],
        'certifications': [],
        'career_path': [],
        'learning_resources': ['Coursera', 'Udemy', 'FreeCodeCamp', 'YouTube tutorials', 'Official documentation']
    }
    
    if 'frontend' in user_categories:
        guidance['recommended_skills'].extend(['TypeScript', 'Next.js', 'GraphQL', 'Testing (Jest)'])
        guidance['certifications'].extend(['React Developer Certification', 'Google UX Design'])
        guidance['career_path'] = ['Junior Frontend Developer', 'Frontend Developer', 'Senior Frontend Developer', 'Frontend Team Lead']
    
    if 'backend' in user_categories:
        guidance['recommended_skills'].extend(['Docker', 'Redis', 'PostgreSQL', 'Microservices'])
        guidance['certifications'].extend(['AWS Certified Developer', 'Oracle Java Certification'])
        guidance['career_path'] = ['Junior Backend Developer', 'Backend Developer', 'Senior Backend Developer', 'Software Architect']
    
    if 'data' in user_categories:
        guidance['recommended_skills'].extend(['TensorFlow', 'Tableau', 'Apache Spark', 'Statistics'])
        guidance['certifications'].extend(['Google Data Analytics', 'IBM Data Science'])
        guidance['career_path'] = ['Data Analyst', 'Data Scientist', 'Senior Data Scientist', 'Data Science Manager']
    
    # Default if no specific category
    if not user_categories:
        guidance['recommended_skills'] = ['Git', 'Agile', 'Problem Solving', 'Communication']
        guidance['certifications'] = ['Google IT Support', 'CompTIA A+']
        guidance['career_path'] = ['Junior Developer', 'Developer', 'Senior Developer', 'Tech Lead']
    
    return guidance


# ─── Resume Analysis ────────────────────────────────────────────────────────

class ResumeAnalysisView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = get_object_or_404(CandidateProfile, user=request.user)
        sync_resume_analysis(profile)
        analysis = get_object_or_404(ResumeAnalysis, candidate=profile)
        return Response(ResumeAnalysisSerializer(analysis).data)


# ─── Job Match ───────────────────────────────────────────────────────────────

class JobMatchView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, job_id):
        profile = get_object_or_404(CandidateProfile, user=request.user)
        job = get_object_or_404(Job, pk=job_id)
        result = calculate_job_match(profile, job)
        JobMatch.objects.update_or_create(
            candidate=profile, job=job,
            defaults={
                'match_percentage': result['match_percentage'],
                'matching_skills': result['matching_skills'],
                'missing_skills': result['missing_skills'],
            }
        )
        return Response(result)


# ─── Candidate Ranking ───────────────────────────────────────────────────────

class CandidateRankingView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, job_id):
        if request.user.role != 'recruiter':
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        job = get_object_or_404(Job, pk=job_id, recruiter=request.user)
        rank_candidates_for_job(job)
        rankings = CandidateRanking.objects.filter(job=job).order_by('rank')
        return Response(CandidateRankingSerializer(rankings, many=True).data)


# ─── AI Question Generator ───────────────────────────────────────────────────

class AIQuestionGeneratorView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role != 'recruiter':
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        job_title = request.data.get('job_title', '').strip()
        skills = request.data.get('skills', [])
        experience_level = request.data.get('experience_level', 'mid').strip()
        if not job_title:
            return Response({'error': 'job_title is required.'}, status=status.HTTP_400_BAD_REQUEST)
        if isinstance(skills, str):
            skills = [s.strip() for s in skills.split(',') if s.strip()]
        
        # Enhanced question generation using both question bank and local AI
        questions = []
        
        # Use services.py function first (question bank)
        try:
            bank_questions = generate_ai_questions(job_title, skills, experience_level)
            questions.extend(bank_questions)
        except Exception as e:
            print(f"Error with question bank: {e}")
        
        # Supplement with local AI generation
        additional_questions = generate_job_questions(job_title, skills, experience_level)
        
        # Combine and deduplicate
        all_questions = questions + additional_questions
        unique_questions = []
        seen = set()
        for q in all_questions:
            if q.lower() not in seen:
                seen.add(q.lower())
                unique_questions.append(q)
        
        # Ensure we have at least 8 questions
        final_questions = unique_questions[:10] if len(unique_questions) >= 8 else unique_questions
        
        obj = AIQuestion.objects.create(
            job_title=job_title, skills=skills,
            experience_level=experience_level, questions=final_questions,
            created_by=request.user,
        )
        return Response(AIQuestionSerializer(obj).data, status=status.HTTP_201_CREATED)

    def get(self, request):
        if request.user.role != 'recruiter':
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        qs = AIQuestion.objects.filter(created_by=request.user).order_by('-created_at')
        return Response(AIQuestionSerializer(qs, many=True).data)


class AIQuestionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        if request.user.role != 'recruiter':
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        obj = get_object_or_404(AIQuestion, pk=pk, created_by=request.user)
        if 'questions' in request.data:
            obj.questions = request.data['questions']
            obj.save()
        return Response(AIQuestionSerializer(obj).data)

    def delete(self, request, pk):
        if request.user.role != 'recruiter':
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        get_object_or_404(AIQuestion, pk=pk, created_by=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ─── Recruiter AI Stats ──────────────────────────────────────────────────────

class RecruiterAIStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'recruiter':
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        jobs = Job.objects.filter(recruiter=request.user)
        top_candidates = (
            CandidateRanking.objects.filter(job__in=jobs)
            .order_by('rank').select_related('candidate__user', 'job')[:5]
        )
        top_list = [{'candidate_name': r.candidate.user.username, 'job_title': r.job.title, 'total_score': r.total_score, 'rank': r.rank} for r in top_candidates]
        skill_gap = JobMatch.objects.filter(job__in=jobs).values_list('missing_skills', flat=True)
        gap_count = {}
        for missing in skill_gap:
            for skill in missing:
                gap_count[skill] = gap_count.get(skill, 0) + 1
        top_gaps = sorted(gap_count.items(), key=lambda x: x[1], reverse=True)[:8]
        return Response({
            'top_candidates': top_list,
            'skill_gap_analysis': [{'skill': k, 'count': v} for k, v in top_gaps],
        })


# ─── Talent Pool ─────────────────────────────────────────────────────────────

class TalentPoolView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'recruiter':
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        qs = TalentPool.objects.filter(recruiter=request.user).select_related('candidate__user')
        skills = request.query_params.get('skills')
        min_exp = request.query_params.get('min_exp')
        min_ats = request.query_params.get('min_ats')
        search = request.query_params.get('search')
        if search:
            qs = qs.filter(candidate__user__username__icontains=search)
        if skills:
            for skill in [s.strip() for s in skills.split(',') if s.strip()]:
                qs = qs.filter(candidate__skills__name__icontains=skill)
        if min_exp:
            try:
                qs = qs.filter(candidate__resume_analysis__experience_years__gte=float(min_exp))
            except Exception:
                pass
        if min_ats:
            try:
                qs = qs.filter(candidate__resume_analysis__ats_score__gte=float(min_ats))
            except Exception:
                pass
        total = qs.count()
        active = qs.filter(contacted=False).count()
        contacted = qs.filter(contacted=True).count()
        return Response({
            'stats': {'total': total, 'active': active, 'contacted': contacted},
            'candidates': TalentPoolSerializer(qs.distinct(), many=True).data,
        })

    def post(self, request):
        if request.user.role != 'recruiter':
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        candidate_id = request.data.get('candidate_id')
        candidate = get_object_or_404(CandidateProfile, pk=candidate_id)
        tp, created = TalentPool.objects.get_or_create(
            recruiter=request.user, candidate=candidate,
            defaults={'notes': request.data.get('notes', '')}
        )
        if not created:
            return Response({'error': 'Candidate already in talent pool.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(TalentPoolSerializer(tp).data, status=status.HTTP_201_CREATED)


class TalentPoolDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        if request.user.role != 'recruiter':
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        tp = get_object_or_404(TalentPool, pk=pk, recruiter=request.user)
        for field in ('notes', 'contacted'):
            if field in request.data:
                setattr(tp, field, request.data[field])
        if request.data.get('contacted'):
            tp.contacted_at = timezone.now()
        tp.save()
        return Response(TalentPoolSerializer(tp).data)

    def delete(self, request, pk):
        if request.user.role != 'recruiter':
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        get_object_or_404(TalentPool, pk=pk, recruiter=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ─── Notifications ───────────────────────────────────────────────────────────

class NotificationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        notifs = Notification.objects.filter(recipient=request.user)
        unread = notifs.filter(is_read=False).count()
        return Response({
            'unread_count': unread,
            'notifications': NotificationSerializer(notifs[:50], many=True).data,
        })


class NotificationMarkReadView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk=None):
        if pk:
            n = get_object_or_404(Notification, pk=pk, recipient=request.user)
            n.is_read = True
            n.save()
        else:
            Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        return Response({'status': 'ok'})


# ─── Offer Response ──────────────────────────────────────────────────────────

class OfferResponseView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, decision_id):
        from interviews.models import CandidateDecision
        profile = get_object_or_404(CandidateProfile, user=request.user)
        decision = get_object_or_404(CandidateDecision, pk=decision_id, interview__candidate=profile, decision='hire')
        if hasattr(decision, 'offer_response'):
            return Response({'error': 'You have already responded to this offer.'}, status=status.HTTP_400_BAD_REQUEST)
        response_val = request.data.get('response')
        if response_val not in ('accepted', 'rejected'):
            return Response({'error': 'Invalid response.'}, status=status.HTTP_400_BAD_REQUEST)
        offer_resp = OfferResponse.objects.create(
            decision=decision,
            response=response_val,
            remarks=request.data.get('remarks', ''),
        )
        event = 'offer_accepted' if response_val == 'accepted' else 'offer_rejected'
        Notification.objects.create(
            recipient=decision.sent_by,
            event=event,
            title=f"Offer {response_val.capitalize()}",
            message=f"{request.user.username} has {response_val} the offer for {decision.interview.job.title if decision.interview.job else 'the position'}.",
        )
        ActivityLog.objects.create(
            candidate=profile,
            event=event,
            description=f"Offer {response_val} for {decision.interview.job.title if decision.interview.job else 'position'}",
        )
        return Response(OfferResponseSerializer(offer_resp).data, status=status.HTTP_201_CREATED)

    def get(self, request, decision_id):
        from interviews.models import CandidateDecision
        profile = get_object_or_404(CandidateProfile, user=request.user)
        decision = get_object_or_404(CandidateDecision, pk=decision_id, interview__candidate=profile)
        if hasattr(decision, 'offer_response'):
            return Response(OfferResponseSerializer(decision.offer_response).data)
        return Response(None)


# ─── Activity Log ────────────────────────────────────────────────────────────

class ActivityLogView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = get_object_or_404(CandidateProfile, user=request.user)
        logs = ActivityLog.objects.filter(candidate=profile)[:50]
        return Response(ActivityLogSerializer(logs, many=True).data)


# ─── Audit Log ───────────────────────────────────────────────────────────────

class AuditLogView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'recruiter':
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        logs = AuditLog.objects.filter(user=request.user)[:100]
        return Response(AuditLogSerializer(logs, many=True).data)


# ─── Hiring Funnel ───────────────────────────────────────────────────────────

class HiringFunnelView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'recruiter':
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        from interviews.models import CandidateDecision, Interview
        from assessments.models import AssessmentResult

        apps = Application.objects.filter(job__recruiter=request.user)
        total = apps.count()

        assessment_completed = AssessmentResult.objects.filter(
            assignment__assessment__recruiter=request.user
        ).values('assignment__candidate').distinct().count()

        interviews = Interview.objects.filter(recruiter=request.user)
        scheduled = interviews.filter(status__in=['scheduled', 'rescheduled']).count()
        completed = interviews.filter(status='completed').count()

        shortlisted = apps.filter(status='shortlisted').count()
        on_hold = apps.filter(status='on_hold').count()

        offers_sent = CandidateDecision.objects.filter(
            interview__recruiter=request.user, decision='hire', delivery_status='sent'
        ).count()

        try:
            hired = OfferResponse.objects.filter(
                decision__interview__recruiter=request.user, response='accepted'
            ).count()
            offer_rejected = OfferResponse.objects.filter(
                decision__interview__recruiter=request.user, response='rejected'
            ).count()
        except Exception:
            hired = 0
            offer_rejected = 0

        def pct(num, denom):
            return round((num / denom * 100), 1) if denom else 0

        return Response({
            'funnel': [
                {'stage': 'Applied', 'count': total},
                {'stage': 'Assessment Completed', 'count': assessment_completed},
                {'stage': 'Interview Scheduled', 'count': scheduled + completed},
                {'stage': 'Interview Completed', 'count': completed},
                {'stage': 'Shortlisted', 'count': shortlisted + on_hold},
                {'stage': 'Offer Sent', 'count': offers_sent},
                {'stage': 'Hired', 'count': hired},
            ],
            'metrics': {
                'hiring_rate': pct(hired, total),
                'offer_acceptance_rate': pct(hired, offers_sent),
                'rejection_rate': pct(offer_rejected, offers_sent),
                'interview_to_offer': pct(offers_sent, completed),
            }
        })


# ─── AI Chat ─────────────────────────────────────────────────────────────────

class ChatHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'candidate':
            return Response([])  # Recruiters have no stored history
        try:
            profile = CandidateProfile.objects.get(user=request.user)
            msgs = ChatHistory.objects.filter(candidate=profile).order_by('created_at')[:100]
            return Response(ChatHistorySerializer(msgs, many=True).data)
        except CandidateProfile.DoesNotExist:
            return Response([])

    def delete(self, request):
        try:
            profile = CandidateProfile.objects.get(user=request.user)
            ChatHistory.objects.filter(candidate=profile).delete()
        except CandidateProfile.DoesNotExist:
            pass
        return Response({'status': 'cleared'})


class AIChatView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user_message = request.data.get('message', '').strip()
        if not user_message:
            return Response({'error': 'Message is required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Candidates use profile-based history; recruiters get session reply only
        if request.user.role == 'candidate':
            profile, _ = CandidateProfile.objects.get_or_create(
                user=request.user,
                defaults={'headline': f"{request.user.username}'s Profile", 'bio': ''}
            )
            ChatHistory.objects.create(candidate=profile, role='user', content=user_message)
            history = list(ChatHistory.objects.filter(candidate=profile).order_by('created_at')[-10:])
            messages = [{'role': m.role, 'content': m.content} for m in history]
            reply = local_ai_chat(messages)
            if not reply:
                reply = "I'm your AI career assistant! Ask me about resume tips, interview prep, skills, or career guidance."
            ChatHistory.objects.create(candidate=profile, role='assistant', content=reply)
        else:
            # Recruiter — no profile needed, just reply
            messages = [{'role': 'user', 'content': user_message}]
            reply = local_ai_recruiter_chat(user_message)
            if not reply:
                reply = "I'm your AI Recruiter Assistant! I can help with job descriptions, interview questions, candidate evaluation, and hiring strategies."

        return Response({'reply': reply})


# ─── Voice Interview ─────────────────────────────────────────────────────────

VOICE_QUESTION_BANK = {
    'frontend': ['Explain the virtual DOM in React.', 'What are React hooks?', 'Difference between CSS Grid and Flexbox?', 'What is TypeScript and why use it?', 'How does browser rendering work?'],
    'backend': ['Explain RESTful API design principles.', 'What is database indexing?', 'Difference between SQL and NoSQL?', 'Explain microservices architecture.', 'What is caching and when to use it?'],
    'fullstack': ['How do you handle authentication in a full-stack app?', 'Explain the MVC pattern.', 'What is CORS and how to handle it?', 'How do you optimize web application performance?', 'Explain CI/CD pipelines.'],
    'java': ['Explain OOP concepts in Java.', 'What is the JVM?', 'Difference between ArrayList and LinkedList?', 'What are Java streams?', 'Explain exception handling in Java.'],
    'python': ['What is a Python decorator?', 'Explain list comprehensions.', 'What is GIL in Python?', 'Difference between deepcopy and shallowcopy?', 'Explain async/await in Python.'],
    'hr': ['Tell me about yourself.', 'Where do you see yourself in 5 years?', 'What is your greatest strength?', 'Describe a challenging situation you overcame.', 'Why do you want to work here?'],
    'custom': ['Tell me about your most recent project.', 'What are your core technical skills?', 'How do you approach problem-solving?', 'Describe your ideal work environment.', 'What motivates you professionally?'],
}


class VoiceInterviewView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        profile = get_object_or_404(CandidateProfile, user=request.user)
        role = request.data.get('role', 'custom')
        difficulty = request.data.get('difficulty', 'intermediate')
        custom_role = request.data.get('custom_role', '')

        # Use local question generation
        skills = list(profile.skills.values_list('name', flat=True)) if hasattr(profile, 'skills') else []
        role_label = custom_role if role == 'custom' else role.replace('_', ' ').title()
        questions = generate_job_questions(role_label, skills, difficulty)

        session = VoiceInterviewSession.objects.create(
            candidate=profile, role=role, custom_role=custom_role,
            difficulty=difficulty, questions=questions,
        )
        return Response(VoiceInterviewSessionSerializer(session).data, status=status.HTTP_201_CREATED)

    def get(self, request):
        profile = get_object_or_404(CandidateProfile, user=request.user)
        sessions = VoiceInterviewSession.objects.filter(candidate=profile).order_by('-created_at')[:10]
        return Response(VoiceInterviewSessionSerializer(sessions, many=True).data)


class VoiceInterviewDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        profile = get_object_or_404(CandidateProfile, user=request.user)
        session = get_object_or_404(VoiceInterviewSession, pk=pk, candidate=profile)

        answer = request.data.get('answer')
        question_index = request.data.get('question_index')
        finalize = request.data.get('finalize', False)

        if answer is not None and question_index is not None:
            answers = session.answers or []
            evaluations = session.evaluations or []
            question_text = session.questions[int(question_index)] if int(question_index) < len(session.questions) else ''

            # Advanced evaluation logic
            evaluation = self.evaluate_answer(question_text, answer)

            while len(answers) <= int(question_index):
                answers.append('')
            while len(evaluations) <= int(question_index):
                evaluations.append({})
            answers[int(question_index)] = answer
            evaluations[int(question_index)] = evaluation
            session.answers = answers
            session.evaluations = evaluations
            session.save()

        if finalize:
            evals = session.evaluations or []
            scores = [e.get('score', 0) for e in evals if e]
            overall = round(sum(scores) / len(scores), 1) if scores else 0
            session.overall_score = overall
            session.technical_score = overall
            session.communication_score = min(overall + 5, 100)
            session.confidence_score = max(overall - 5, 0)
            session.readiness_score = round((overall * 0.6 + len(evals) / max(len(session.questions), 1) * 40), 1)
            session.completed = True
            session.completed_at = timezone.now()
            session.save()

        return Response(VoiceInterviewSessionSerializer(session).data)

    def evaluate_answer(self, question, answer):
        """Comprehensive answer evaluation"""
        if not answer or not answer.strip():
            return {
                'score': 10,
                'feedback': 'No answer provided. Please provide a response to demonstrate your knowledge.',
                'strengths': [],
                'weaknesses': ['No response given'],
                'suggested_answer': f'For "{question}", provide a structured answer with examples and technical details.'
            }
        
        answer_lower = answer.lower().strip()
        question_lower = question.lower().strip()
        answer_words = answer.split()
        answer_length = len(answer_words)
        
        # Initialize scoring
        base_score = 30  # Base score for providing an answer
        
        # Length analysis
        if answer_length < 5:
            base_score -= 15
        elif answer_length < 15:
            base_score -= 5
        elif answer_length > 30:
            base_score += 15
        elif answer_length > 50:
            base_score += 25
        
        # Content quality analysis
        strengths = []
        weaknesses = []
        
        # Check for technical accuracy based on question type
        technical_score = self.assess_technical_accuracy(question_lower, answer_lower)
        base_score += technical_score
        
        # Structure and clarity
        has_structure = any(word in answer_lower for word in [
            'first', 'second', 'then', 'finally', 'because', 'however', 
            'for example', 'such as', 'in my experience', 'additionally'
        ])
        
        if has_structure:
            base_score += 10
            strengths.append('Well-structured response')
        else:
            weaknesses.append('Could benefit from better structure')
        
        # Examples and specificity
        has_examples = any(word in answer_lower for word in [
            'example', 'instance', 'project', 'experience', 'worked on', 
            'built', 'implemented', 'used', 'time when', 'once'
        ])
        
        if has_examples:
            base_score += 15
            strengths.append('Includes concrete examples')
        else:
            weaknesses.append('Add specific examples from your experience')
        
        # Technical depth
        technical_terms = self.count_technical_terms(question_lower, answer_lower)
        if technical_terms > 2:
            base_score += 10
            strengths.append('Good technical vocabulary')
        elif technical_terms == 0:
            weaknesses.append('Include more technical details')
        
        # Communication quality
        if not any(word in answer_lower for word in ['um', 'uh', 'like', 'you know']):
            strengths.append('Clear communication')
        
        # Check for wrong or irrelevant information
        if self.contains_incorrect_info(question_lower, answer_lower):
            base_score -= 20
            weaknesses.append('Contains incorrect or irrelevant information')
        
        # Cap the score
        final_score = max(10, min(95, base_score))
        
        # Generate feedback
        if final_score >= 80:
            feedback = 'Excellent answer with strong technical knowledge and clear communication.'
        elif final_score >= 70:
            feedback = 'Good answer demonstrating solid understanding with room for minor improvements.'
        elif final_score >= 60:
            feedback = 'Adequate answer but could be improved with more detail and examples.'
        elif final_score >= 40:
            feedback = 'Basic answer provided but lacks depth and technical accuracy.'
        else:
            feedback = 'Answer needs significant improvement in accuracy and detail.'
        
        # Generate suggested improvement
        suggested_answer = self.generate_suggested_answer(question_lower, weaknesses)
        
        return {
            'score': final_score,
            'feedback': feedback,
            'strengths': strengths or ['Response provided'],
            'weaknesses': weaknesses or ['Consider adding more detail'],
            'suggested_answer': suggested_answer
        }
    
    def assess_technical_accuracy(self, question, answer):
        """Assess technical accuracy based on question type"""
        score = 0
        
        # React questions
        if any(term in question for term in ['react', 'jsx', 'hooks', 'component']):
            if any(term in answer for term in ['component', 'jsx', 'props', 'state', 'hook']):
                score += 15
            if any(term in answer for term in ['usestate', 'useeffect', 'virtual dom', 'render']):
                score += 10
            if any(wrong in answer for wrong in ['angular', 'vue directive', 'template']):
                score -= 15
        
        # Python questions
        elif any(term in question for term in ['python', 'decorator', 'gil', 'list']):
            if any(term in answer for term in ['python', 'function', 'variable', 'object']):
                score += 15
            if any(term in answer for term in ['gil', 'global interpreter lock', 'thread']):
                score += 10
            if any(wrong in answer for wrong in ['java class', 'c++ pointer']):
                score -= 15
        
        # JavaScript questions
        elif any(term in question for term in ['javascript', 'closure', 'promise', 'async']):
            if any(term in answer for term in ['function', 'variable', 'callback', 'promise']):
                score += 15
            if any(term in answer for term in ['closure', 'scope', 'hoisting', 'event loop']):
                score += 10
        
        # General programming
        elif any(term in question for term in ['algorithm', 'data structure', 'complexity']):
            if any(term in answer for term in ['algorithm', 'time', 'space', 'complexity', 'big o']):
                score += 15
        
        # Behavioral questions
        elif any(term in question for term in ['tell me', 'describe', 'experience', 'challenge']):
            if any(term in answer for term in ['project', 'team', 'problem', 'solution', 'learned']):
                score += 10
        
        return score
    
    def count_technical_terms(self, question, answer):
        """Count relevant technical terms"""
        technical_terms = [
            'api', 'database', 'server', 'client', 'framework', 'library',
            'algorithm', 'function', 'method', 'class', 'object', 'variable',
            'array', 'string', 'boolean', 'integer', 'json', 'xml', 'http',
            'rest', 'graphql', 'sql', 'nosql', 'cache', 'optimization',
            'performance', 'security', 'authentication', 'authorization'
        ]
        
        count = 0
        for term in technical_terms:
            if term in answer:
                count += 1
        return count
    
    def contains_incorrect_info(self, question, answer):
        """Check for obviously incorrect information"""
        # Common misconceptions
        incorrect_patterns = [
            ('react' in question and any(wrong in answer for wrong in [
                'react is a library by google', 'react uses templates',
                'react doesn\'t use virtual dom'
            ])),
            ('python' in question and any(wrong in answer for wrong in [
                'python is compiled', 'python doesn\'t have classes',
                'python is only for web development'
            ])),
            ('javascript' in question and any(wrong in answer for wrong in [
                'javascript is java', 'javascript only runs in browsers',
                'javascript is compiled'
            ]))
        ]
        
        return any(incorrect_patterns)
    
    def generate_suggested_answer(self, question, weaknesses):
        """Generate improvement suggestions"""
        suggestions = []
        
        if 'Could benefit from better structure' in weaknesses:
            suggestions.append('Structure your answer with clear points (First, Second, Finally)')
        
        if 'Add specific examples from your experience' in weaknesses:
            suggestions.append('Include a specific project or situation where you applied this knowledge')
        
        if 'Include more technical details' in weaknesses:
            suggestions.append('Use technical terminology and explain the underlying concepts')
        
        if 'Contains incorrect or irrelevant information' in weaknesses:
            suggestions.append('Focus on accurate, relevant information related to the question')
        
        base_suggestion = f'For "{question}": '
        
        if suggestions:
            return base_suggestion + '; '.join(suggestions) + '.'
        else:
            return base_suggestion + 'Expand your answer with more depth, examples, and technical details.'

    def get(self, request, pk):
        profile = get_object_or_404(CandidateProfile, user=request.user)
        session = get_object_or_404(VoiceInterviewSession, pk=pk, candidate=profile)
        return Response(VoiceInterviewSessionSerializer(session).data)


# ─── Export ──────────────────────────────────────────────────────────────────

class ExportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django.http import HttpResponse
        export_type = request.query_params.get('type', 'applicants')
        fmt = request.query_params.get('format', 'csv')

        if request.user.role != 'recruiter':
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

        rows = []
        if export_type == 'applicants':
            apps = Application.objects.filter(job__recruiter=request.user).select_related('candidate__user', 'job')
            rows = [['Candidate', 'Email', 'Job', 'Status', 'Applied At']]
            rows += [[a.candidate.user.username, a.candidate.user.email, a.job.title, a.status, str(a.applied_at)] for a in apps]
        elif export_type == 'hiring':
            from interviews.models import CandidateDecision
            decisions = CandidateDecision.objects.filter(interview__recruiter=request.user).select_related('interview__candidate__user', 'interview__job', 'sent_by')
            rows = [['Candidate', 'Job', 'Decision', 'Sent By', 'Sent At', 'Status']]
            rows += [[d.interview.candidate.user.username, d.interview.job.title if d.interview.job else '', d.decision, d.sent_by.username, str(d.sent_at), d.delivery_status] for d in decisions]

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerows(rows)
        response = HttpResponse(output.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{export_type}_export.csv"'
        return response


# ─── Company Public Page ─────────────────────────────────────────────────────

class CompanyPublicView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        recruiter_id = request.query_params.get('recruiter_id')
        from accounts.models import User
        if recruiter_id:
            recruiter = get_object_or_404(User, pk=recruiter_id, role='recruiter')
        else:
            recruiter = User.objects.filter(role='recruiter').first()
        if not recruiter:
            return Response({'error': 'Not found'}, status=404)

        jobs = Job.objects.filter(recruiter=recruiter, status='open')
        total_hired = OfferResponse.objects.filter(
            decision__interview__recruiter=recruiter, response='accepted'
        ).count()

        return Response({
            'company': jobs.first().company if jobs.exists() else recruiter.username,
            'recruiter': recruiter.username,
            'open_jobs': [{'id': j.id, 'title': j.title, 'location': j.location, 'job_type': j.job_type} for j in jobs],
            'stats': {
                'open_positions': jobs.count(),
                'total_hired': total_hired,
            }
        })


# ─── Recruiter AI Assistant ──────────────────────────────────────────────────

class RecruiterAssistantView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role != 'recruiter':
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        task = request.data.get('task', '')
        context = request.data.get('context', '')
        if not task:
            return Response({'error': 'task is required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Local AI assistant logic
        if task == 'job_description':
            role_parts = context.lower().split()
            
            # Extract role and seniority
            seniority = 'Mid-Level'
            if any(word in role_parts for word in ['senior', 'sr', 'lead', 'principal']):
                seniority = 'Senior'
            elif any(word in role_parts for word in ['junior', 'jr', 'entry', 'graduate']):
                seniority = 'Junior'
            
            # Determine tech stack
            tech_stack = []
            if any(word in role_parts for word in ['frontend', 'react', 'javascript']):
                tech_stack = ['React', 'JavaScript', 'HTML/CSS', 'TypeScript']
            elif any(word in role_parts for word in ['backend', 'python', 'django']):
                tech_stack = ['Python', 'Django', 'PostgreSQL', 'REST APIs']
            elif any(word in role_parts for word in ['fullstack', 'full-stack']):
                tech_stack = ['JavaScript', 'React', 'Node.js', 'SQL']
            elif any(word in role_parts for word in ['data', 'scientist', 'analyst']):
                tech_stack = ['Python', 'SQL', 'Pandas', 'Machine Learning']
            else:
                tech_stack = ['Programming', 'Problem Solving', 'Version Control']
            
            result = f"""
**{seniority} {context}**

**About the Role:**
We are seeking a talented {seniority} {context} to join our growing technology team. You will be responsible for designing, developing, and maintaining high-quality software solutions that drive our business forward.

**Key Responsibilities:**
• Develop and maintain scalable software applications
• Collaborate with cross-functional teams to deliver features
• Write clean, efficient, and well-documented code
• Participate in code reviews and technical discussions
• {'Mentor junior developers and' if seniority == 'Senior' else 'Learn from'} contribute to team knowledge sharing

**Required Skills:**
• {' years' if seniority == 'Senior' else '2+ years' if seniority == 'Mid-Level' else '0-2 years'} of experience in software development
• Proficiency in: {', '.join(tech_stack)}
• Strong problem-solving and analytical skills
• Excellent communication and teamwork abilities
• Bachelor's degree in Computer Science or related field (or equivalent experience)

**Nice to Have:**
• Experience with cloud platforms (AWS, Azure)
• Knowledge of DevOps practices and CI/CD
• Contribution to open-source projects
• Relevant certifications

**What We Offer:**
• Competitive salary and benefits
• Professional development opportunities
• Flexible working arrangements
• Collaborative and innovative work environment
"""
        
        elif task == 'interview_questions':
            skills = [s.strip() for s in context.split(',') if s.strip()]
            questions = generate_ai_questions(context, skills, 'mid')
            result = f"**Interview Questions for {context}:**\n\n" + "\n".join([f"{i+1}. {q}" for i, q in enumerate(questions)])
        
        elif task == 'hiring_feedback':
            result = f"""
**Hiring Decision Feedback**

Based on the evaluation: {context[:200]}...

**Recommendation:** [Hire/Hold/Pass]

**Strengths:**
• Technical competency demonstrated
• Good communication skills
• Cultural fit with team values

**Areas for Development:**
• Could benefit from additional experience in [specific area]
• Opportunity to grow leadership skills

**Next Steps:**
• [If Hire] Proceed with offer preparation
• [If Hold] Schedule follow-up interview
• [If Pass] Provide constructive feedback to candidate

**Salary Recommendation:** Based on experience level and market rates
"""
        
        elif task == 'candidate_evaluation':
            result = f"""
**Candidate Evaluation Summary**

**Candidate:** [Name from context]
**Position:** [Role]
**Interview Date:** [Date]

**Technical Assessment:** 
{context[:200]}...

**Overall Rating:** [Score]/10

**Key Strengths:**
• Strong technical foundation
• Problem-solving approach
• Communication clarity

**Development Areas:**
• [Specific technical gaps]
• [Soft skill improvements]

**Cultural Fit:** Aligns well with team dynamics and company values

**Recommendation:** Move forward with next round/Extend offer/Hold for future opportunities
"""
        
        else:
            result = f"AI Assistant Result for '{task}': {context[:200]}... [Enhanced local analysis provided]"
        
        return Response({'result': result})


# ─── Career Guidance ─────────────────────────────────────────────────────────

class CareerGuidanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = get_object_or_404(CandidateProfile, user=request.user)
        skills = list(profile.skills.values_list('name', flat=True))
        
        # Use local career guidance generation
        guidance = generate_career_guidance(skills)
        return Response(guidance)


# ─── Cover Letter ────────────────────────────────────────────────────────────

class CoverLetterView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        profile = get_object_or_404(CandidateProfile, user=request.user)
        job_description = request.data.get('job_description', '')
        skills = list(profile.skills.values_list('name', flat=True))
        experience = list(profile.experience.values('title', 'company'))
        
        # Generate cover letter using local AI
        top_skills = skills[:5]  # Top 5 skills
        recent_exp = experience[:2] if experience else []
        
        # Extract key requirements from job description
        job_keywords = [word.strip() for word in job_description.lower().split() 
                       if word.strip() and len(word) > 3 and word.isalpha()][:10]
        matching_skills = [s for s in top_skills if s.lower() in job_keywords]
        
        cover_letter = f"""Dear Hiring Manager,

I am writing to express my strong interest in the position described in your job posting. With my background in {', '.join(top_skills[:3]) if top_skills else 'software development'}, I am confident I can contribute effectively to your team.

{'In my recent role' if recent_exp else 'Through my experience'} {'at ' + recent_exp[0]['company'] if recent_exp else 'in software development'}, I have developed expertise in {', '.join(matching_skills[:3]) if matching_skills else ', '.join(top_skills[:3]) if top_skills else 'various technologies'}, which directly aligns with your requirements.

Key qualifications I bring:
{'• ' + chr(10).join([f"Proficiency in {skill}" for skill in top_skills[:4]]) if top_skills else '• Strong technical foundation'}{'• ' + str(len(experience)) + '+ years of professional experience' if experience else '• Eager to apply my skills in a professional setting'}
{'• Proven track record at ' + ', '.join([exp['company'] for exp in recent_exp[:2]]) if recent_exp else '• Strong problem-solving abilities'}

I am excited about the opportunity to discuss how my skills and experience can contribute to your team's success. Thank you for considering my application.

Best regards,
{request.user.first_name or request.user.username}"""
        
        return Response({'cover_letter': cover_letter})


# ─── Resume Tailoring ────────────────────────────────────────────────────────

class ResumeTailoringView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        profile = get_object_or_404(CandidateProfile, user=request.user)
        job_description = request.data.get('job_description', '')
        skills = list(profile.skills.values_list('name', flat=True))
        
        # Local analysis logic
        job_words = set(word.lower().strip() for word in job_description.replace(',', ' ').split() 
                       if len(word) > 2 and word.isalpha())
        
        # Tech keywords commonly found in job descriptions
        tech_keywords = {
            'python', 'javascript', 'react', 'node', 'django', 'flask', 'sql', 'postgresql', 
            'mysql', 'mongodb', 'redis', 'aws', 'azure', 'docker', 'kubernetes', 'git', 
            'html', 'css', 'typescript', 'java', 'spring', 'angular', 'vue', 'api', 'rest', 
            'graphql', 'microservices', 'testing', 'jest', 'pytest', 'agile', 'scrum',
            'linux', 'nginx', 'jenkins', 'ci/cd', 'devops', 'machine learning', 'ai'
        }
        
        my_skills_lower = set(s.lower() for s in skills)
        job_tech_words = job_words & tech_keywords
        
        matching_keywords = list(my_skills_lower & job_tech_words)
        missing_keywords = list(job_tech_words - my_skills_lower)
        
        # Calculate ATS score
        base_score = 40
        if matching_keywords:
            base_score += min(len(matching_keywords) * 8, 40)  # Max 40 points for matches
        if len(skills) >= 5:
            base_score += 10  # Bonus for having multiple skills
        if any(word in job_description.lower() for word in ['bachelor', 'degree', 'education']):
            if profile.education.exists():
                base_score += 10
        
        ats_score = min(base_score, 90)  # Cap at 90
        
        # Generate suggestions
        suggestions = [
            "Use action verbs like 'developed', 'implemented', 'optimized'",
            "Include quantifiable achievements (e.g., 'Improved performance by 30%')",
            "Tailor your summary to match the job requirements"
        ]
        
        if missing_keywords:
            suggestions.append(f"Consider adding these relevant keywords: {', '.join(missing_keywords[:5])}")
        if ats_score < 70:
            suggestions.append("Add more technical skills that match the job description")
            suggestions.append("Include specific project examples")
        if len(skills) < 5:
            suggestions.append("Expand your skills section with relevant technologies")
            
        return Response({
            'missing_keywords': missing_keywords[:8],
            'matching_keywords': matching_keywords[:8],
            'ats_suggestions': suggestions,
            'score': ats_score
        })


# ─── Profile Completion ──────────────────────────────────────────────────────

class ProfileCompletionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = get_object_or_404(CandidateProfile, user=request.user)
        sections = {
            'Personal Information': bool(profile.headline and profile.bio and profile.location),
            'Education': profile.education.exists(),
            'Skills': profile.skills.exists(),
            'Experience': profile.experience.exists(),
            'Resume': profile.resumes.filter(is_active=True).exists(),
            'Certifications': profile.certifications.exists() if hasattr(profile, 'certifications') else False,
            'Portfolio': bool(profile.github or profile.linkedin),
        }
        completed = sum(sections.values())
        total = len(sections)
        percentage = round((completed / total) * 100)
        missing = [k for k, v in sections.items() if not v]
        return Response({'percentage': percentage, 'sections': sections, 'missing': missing, 'completed': completed, 'total': total})


# ─── Hiring Insights ────────────────────────────────────────────────────────

class HiringInsightsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'recruiter':
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        from django.db.models import Count
        jobs = Job.objects.filter(recruiter=request.user)

        skill_counts = {}
        for job in jobs:
            for s in [sk.strip().lower() for sk in job.skills_required.split(',') if sk.strip()]:
                skill_counts[s] = skill_counts.get(s, 0) + 1
        top_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:8]

        monthly_apps = (
            Application.objects.filter(job__recruiter=request.user)
            .extra(select={'month': "strftime('%Y-%m', applied_at)"})
            .values('month').annotate(count=Count('id')).order_by('month')[:6]
        )

        return Response({
            'most_hired_skills': [{'skill': k, 'count': v} for k, v in top_skills],
            'monthly_applications': list(monthly_apps),
        })


# ─── Career Twin ────────────────────────────────────────────────────────────

class CareerTwinView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = get_object_or_404(CandidateProfile, user=request.user)
        skills = list(profile.skills.values_list('name', flat=True))
        skills_lower = set(s.lower() for s in skills)
        
        # Determine current level based on skills
        frontend_skills = {'javascript', 'react', 'html', 'css', 'typescript'}
        backend_skills = {'python', 'django', 'sql', 'api', 'postgresql'}
        cloud_skills = {'aws', 'docker', 'kubernetes', 'devops'}
        data_skills = {'machine learning', 'pandas', 'numpy', 'tensorflow'}
        
        skill_coverage = {
            'frontend': len(skills_lower & frontend_skills) / len(frontend_skills),
            'backend': len(skills_lower & backend_skills) / len(backend_skills),
            'cloud': len(skills_lower & cloud_skills) / len(cloud_skills),
            'data': len(skills_lower & data_skills) / len(data_skills)
        }
        
        # Determine primary path
        primary_path = max(skill_coverage.items(), key=lambda x: x[1])[0]
        coverage = max(skill_coverage.values())
        
        # Generate roadmap based on skill level
        if coverage >= 0.6:  # Senior level
            six_month = {
                'skills_to_learn': ['System Design', 'Microservices', 'Performance Optimization'],
                'target_role': 'Senior Developer',
                'actions': ['Lead a major project', 'Mentor junior developers', 'Present at tech meetups']
            }
            one_year = {
                'skills_to_learn': ['Architecture Patterns', 'Team Leadership', 'Technical Strategy'],
                'target_role': 'Tech Lead / Engineering Manager',
                'actions': ['Manage a team', 'Drive technical decisions', 'Cross-functional collaboration']
            }
            three_year = {
                'skills_to_learn': ['Product Strategy', 'Business Acumen', 'Organizational Leadership'],
                'target_role': 'Engineering Director / CTO',
                'actions': ['Scale engineering organization', 'Define technical vision', 'Strategic planning'],
                'estimated_salary_range': '$120K - $200K+'
            }
        elif coverage >= 0.3:  # Mid level
            six_month = {
                'skills_to_learn': ['Advanced Frameworks', 'Testing', 'CI/CD'],
                'target_role': 'Mid-Level Developer',
                'actions': ['Complete 2-3 major features', 'Improve code quality', 'Learn best practices']
            }
            one_year = {
                'skills_to_learn': ['System Design Basics', 'Database Optimization', 'Monitoring'],
                'target_role': 'Senior Developer',
                'actions': ['Lead small projects', 'Code reviews', 'Technical documentation']
            }
            three_year = {
                'skills_to_learn': ['Team Leadership', 'Architecture', 'Mentoring'],
                'target_role': 'Tech Lead',
                'actions': ['Mentor others', 'Technical strategy', 'Cross-team collaboration'],
                'estimated_salary_range': '$80K - $140K'
            }
        else:  # Junior level
            six_month = {
                'skills_to_learn': ['Core Technologies', 'Git Workflow', 'Debugging'],
                'target_role': 'Junior Developer',
                'actions': ['Build 3+ projects', 'Contribute to team', 'Learn company processes']
            }
            one_year = {
                'skills_to_learn': ['Advanced Features', 'Testing', 'Code Review'],
                'target_role': 'Developer',
                'actions': ['Own feature development', 'Improve efficiency', 'Seek feedback']
            }
            three_year = {
                'skills_to_learn': ['System Design', 'Performance', 'Leadership'],
                'target_role': 'Senior Developer',
                'actions': ['Technical ownership', 'Mentor juniors', 'Drive initiatives'],
                'estimated_salary_range': '$60K - $100K'
            }
        
        # Customize based on primary path
        if primary_path == 'frontend':
            six_month['skills_to_learn'].extend(['Next.js', 'State Management'])
        elif primary_path == 'backend':
            six_month['skills_to_learn'].extend(['API Design', 'Database Design'])
        elif primary_path == 'cloud':
            six_month['skills_to_learn'].extend(['Infrastructure as Code', 'Monitoring'])
        elif primary_path == 'data':
            six_month['skills_to_learn'].extend(['MLOps', 'Data Pipeline'])
        
        return Response({
            'six_month': six_month,
            'one_year': one_year,
            'three_year': three_year
        })


# ─── Skill Gap ───────────────────────────────────────────────────────────────

class SkillGapView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        profile = get_object_or_404(CandidateProfile, user=request.user)
        target_role = request.data.get('target_role', '')
        my_skills = list(profile.skills.values_list('name', flat=True))
        my_skills_lower = set(s.lower() for s in my_skills)
        
        # Define skill requirements for different roles
        role_requirements = {
            'frontend developer': ['javascript', 'react', 'html', 'css', 'typescript', 'git', 'responsive design'],
            'backend developer': ['python', 'sql', 'api', 'django', 'postgresql', 'git', 'testing'],
            'full stack developer': ['javascript', 'python', 'react', 'sql', 'api', 'git', 'html', 'css'],
            'data scientist': ['python', 'sql', 'pandas', 'machine learning', 'statistics', 'jupyter', 'git'],
            'devops engineer': ['aws', 'docker', 'kubernetes', 'linux', 'ci/cd', 'terraform', 'git'],
            'mobile developer': ['react native', 'javascript', 'mobile', 'api', 'git', 'testing'],
            'software engineer': ['programming', 'algorithms', 'data structures', 'git', 'testing', 'api'],
        }
        
        # Find matching role or use generic requirements
        required_skills = []
        target_lower = target_role.lower()
        for role, skills in role_requirements.items():
            if any(keyword in target_lower for keyword in role.split()):
                required_skills = skills
                break
        
        if not required_skills:
            # Generic tech skills
            required_skills = ['programming', 'git', 'problem solving', 'testing', 'api', 'database']
        
        required_set = set(required_skills)
        missing_skills = list(required_set - my_skills_lower)
        
        # Prioritize missing skills
        priority_map = {
            'high': ['javascript', 'python', 'react', 'sql', 'git', 'api'],
            'medium': ['html', 'css', 'testing', 'docker', 'aws', 'typescript'],
            'low': ['linux', 'ci/cd', 'kubernetes', 'mongodb', 'redis']
        }
        
        priorities = {}
        for skill in missing_skills:
            for level, skill_list in priority_map.items():
                if skill in skill_list:
                    priorities[skill] = level
                    break
            if skill not in priorities:
                priorities[skill] = 'medium'
        
        # Generate learning path
        learning_path = [
            "1. Master the fundamentals of your missing high-priority skills",
            "2. Build projects that demonstrate these skills",
            "3. Contribute to open-source projects",
            "4. Get certified in relevant technologies",
            "5. Network with professionals in your target role"
        ]
        
        if 'programming' in missing_skills or not my_skills:
            learning_path.insert(1, "1.5. Practice coding problems on platforms like LeetCode")
        
        return Response({
            'missing_skills': missing_skills[:10],
            'recommended_skills': required_skills,
            'learning_path': learning_path,
            'priority': priorities
        })


# ─── Mock Interview ──────────────────────────────────────────────────────────

class MockInterviewView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        profile = get_object_or_404(CandidateProfile, user=request.user)
        action = request.data.get('action', 'generate')

        if action == 'generate':
            skills = list(profile.skills.values_list('name', flat=True))
            role = request.data.get('role', 'Software Developer')
            
            # Generate questions using local AI
            questions_list = generate_job_questions(role, skills, 'intermediate')
            questions = []
            
            for i, q in enumerate(questions_list):
                q_type = 'behavioral'
                difficulty = 'medium'
                
                # Classify question type
                if any(tech in q.lower() for tech in ['explain', 'what is', 'how does', 'difference', 'implement']):
                    q_type = 'technical'
                elif any(hr in q.lower() for hr in ['tell me', 'describe yourself', 'why', 'where do you']):
                    q_type = 'hr'
                
                # Set difficulty based on question complexity
                if any(easy in q.lower() for easy in ['what is', 'define', 'basic']):
                    difficulty = 'easy'
                elif any(hard in q.lower() for hard in ['optimize', 'design', 'scale', 'architect']):
                    difficulty = 'hard'
                
                questions.append({
                    'question': q,
                    'type': q_type,
                    'difficulty': difficulty
                })
            
            return Response({'questions': questions})

        elif action == 'evaluate':
            question = request.data.get('question', '')
            answer = request.data.get('answer', '')
            
            # Comprehensive evaluation
            evaluation = self.evaluate_mock_answer(question, answer)
            return Response(evaluation)

        return Response({'error': 'Invalid action.'}, status=status.HTTP_400_BAD_REQUEST)
    
    def evaluate_mock_answer(self, question, answer):
        """Comprehensive mock interview answer evaluation"""
        if not answer or not answer.strip():
            return {
                'score': 5,
                'technical_accuracy': 10,
                'communication': 15,
                'confidence': 10,
                'clarity': 10,
                'completeness': 5,
                'strengths': [],
                'weaknesses': ['No answer provided'],
                'suggested_better_answer': 'Please provide a complete answer to demonstrate your knowledge and communication skills.'
            }
        
        answer_lower = answer.lower().strip()
        question_lower = question.lower().strip()
        answer_words = answer.split()
        answer_length = len(answer_words)
        
        # Base scores
        scores = {
            'score': 40,
            'technical_accuracy': 50,
            'communication': 50,
            'confidence': 50,
            'clarity': 50,
            'completeness': 40
        }
        
        strengths = []
        weaknesses = []
        
        # Length analysis
        if answer_length < 10:
            scores['completeness'] -= 20
            scores['score'] -= 15
            weaknesses.append('Answer is too brief')
        elif answer_length > 30:
            scores['completeness'] += 20
            scores['communication'] += 10
            strengths.append('Comprehensive response')
        
        # Structure analysis
        has_structure = any(marker in answer_lower for marker in [
            'first', 'second', 'third', 'then', 'next', 'finally',
            'initially', 'subsequently', 'in conclusion', 'to summarize'
        ])
        
        if has_structure:
            scores['clarity'] += 20
            scores['communication'] += 15
            strengths.append('Well-structured answer')
        else:
            weaknesses.append('Could use better structure (first, then, finally)')
        
        # STAR method for behavioral questions
        if any(behavioral in question_lower for behavioral in [
            'tell me about', 'describe a time', 'give an example', 'situation'
        ]):
            star_elements = {
                'situation': any(s in answer_lower for s in ['situation', 'context', 'background', 'project']),
                'task': any(t in answer_lower for t in ['task', 'goal', 'objective', 'needed to']),
                'action': any(a in answer_lower for a in ['action', 'did', 'implemented', 'used', 'applied']),
                'result': any(r in answer_lower for r in ['result', 'outcome', 'achieved', 'improved', 'increased'])
            }
            
            star_count = sum(star_elements.values())
            if star_count >= 3:
                scores['technical_accuracy'] += 20
                scores['completeness'] += 15
                strengths.append('Follows STAR method')
            elif star_count >= 2:
                scores['completeness'] += 10
                strengths.append('Good storytelling structure')
            else:
                weaknesses.append('Use STAR method: Situation, Task, Action, Result')
        
        # Technical accuracy for technical questions
        if any(tech in question_lower for tech in [
            'explain', 'how does', 'what is', 'difference between', 'implement'
        ]):
            tech_score = self.assess_technical_content(question_lower, answer_lower)
            scores['technical_accuracy'] += tech_score
            
            if tech_score > 15:
                strengths.append('Strong technical knowledge')
            elif tech_score < 5:
                weaknesses.append('Needs more technical detail')
        
        # Examples and specificity
        has_examples = any(example in answer_lower for example in [
            'example', 'for instance', 'such as', 'like when', 'in my experience',
            'project', 'worked on', 'built', 'developed', 'implemented'
        ])
        
        if has_examples:
            scores['confidence'] += 15
            scores['technical_accuracy'] += 10
            strengths.append('Uses concrete examples')
        else:
            weaknesses.append('Add specific examples from your experience')
        
        # Communication quality
        filler_words = len([w for w in answer_words if w.lower() in ['um', 'uh', 'like', 'you know', 'basically']])
        if filler_words == 0:
            scores['communication'] += 15
            strengths.append('Clear, professional communication')
        elif filler_words > 3:
            scores['communication'] -= 10
            weaknesses.append('Minimize filler words (um, uh, like)')
        
        # Confidence indicators
        confident_phrases = any(phrase in answer_lower for phrase in [
            'i believe', 'i\'m confident', 'i know', 'i have experience',
            'i successfully', 'i achieved', 'i led', 'i managed'
        ])
        
        uncertain_phrases = any(phrase in answer_lower for phrase in [
            'i think maybe', 'i\'m not sure', 'i guess', 'probably',
            'i might', 'not really sure'
        ])
        
        if confident_phrases:
            scores['confidence'] += 15
            strengths.append('Confident delivery')
        elif uncertain_phrases:
            scores['confidence'] -= 15
            weaknesses.append('Be more confident in your responses')
        
        # Question relevance
        if self.is_answer_relevant(question_lower, answer_lower):
            scores['technical_accuracy'] += 10
        else:
            scores['technical_accuracy'] -= 20
            weaknesses.append('Answer doesn\'t fully address the question')
        
        # Cap all scores
        for key in scores:
            scores[key] = max(5, min(95, scores[key]))
        
        # Generate improvement suggestions
        suggestions = self.generate_mock_suggestions(question_lower, weaknesses, strengths)
        
        return {
            **scores,
            'strengths': strengths or ['Provided a response'],
            'weaknesses': weaknesses or ['Minor improvements possible'],
            'suggested_better_answer': suggestions
        }
    
    def assess_technical_content(self, question, answer):
        """Assess technical content quality"""
        score = 0
        
        # Technology-specific assessment
        if 'react' in question:
            if any(term in answer for term in ['component', 'jsx', 'props', 'state', 'hook', 'render']):
                score += 15
            if any(advanced in answer for advanced in ['virtual dom', 'lifecycle', 'context', 'reducer']):
                score += 10
        
        elif 'python' in question:
            if any(term in answer for term in ['function', 'class', 'object', 'variable', 'list', 'dictionary']):
                score += 15
            if any(advanced in answer for advanced in ['decorator', 'generator', 'comprehension', 'gil']):
                score += 10
        
        elif 'javascript' in question:
            if any(term in answer for term in ['function', 'variable', 'object', 'array', 'callback']):
                score += 15
            if any(advanced in answer for advanced in ['closure', 'prototype', 'async', 'promise']):
                score += 10
        
        # General technical terms
        technical_terms = ['algorithm', 'data structure', 'api', 'database', 'performance', 
                          'optimization', 'security', 'testing', 'debugging']
        
        term_count = sum(1 for term in technical_terms if term in answer)
        score += min(term_count * 3, 15)
        
        return score
    
    def is_answer_relevant(self, question, answer):
        """Check if answer is relevant to the question"""
        question_keywords = set(question.split())
        answer_keywords = set(answer.split())
        
        # Remove common words
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'is', 'are', 'was', 'were', 'to', 'of', 'in', 'on', 'at'}
        question_keywords -= common_words
        answer_keywords -= common_words
        
        # Check overlap
        overlap = len(question_keywords & answer_keywords)
        return overlap >= 1 or len(answer) > 50  # Relevant if keywords match or detailed answer
    
    def generate_mock_suggestions(self, question, weaknesses, strengths):
        """Generate specific improvement suggestions"""
        suggestions = []
        
        if 'Answer is too brief' in weaknesses:
            suggestions.append('Expand your answer with more details and examples')
        
        if 'Could use better structure' in weaknesses:
            suggestions.append('Use a clear structure: introduce your point, explain it, give an example')
        
        if 'Use STAR method' in weaknesses:
            suggestions.append('For behavioral questions, use STAR: Situation, Task, Action, Result')
        
        if 'Needs more technical detail' in weaknesses:
            suggestions.append('Include specific technical concepts, tools, and methodologies')
        
        if 'Add specific examples' in weaknesses:
            suggestions.append('Share a concrete example from your projects or experience')
        
        if 'Be more confident' in weaknesses:
            suggestions.append('Use confident language: "I successfully..." instead of "I think maybe..."')
        
        base_suggestion = 'To improve your answer: '
        if suggestions:
            return base_suggestion + '. '.join(suggestions) + '.'
        else:
            return 'Great answer! Continue practicing to maintain this quality in real interviews.'
