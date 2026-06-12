from .models import JobMatch, CandidateRanking, ResumeAnalysis
from candidates.models import CandidateProfile
from jobs.models import Job, Application


QUESTION_BANK = {
    'python': {
        'junior': [
            'What is the difference between a list and a tuple in Python?',
            'Explain what a Python dictionary is and give an example.',
            'What are Python decorators?',
        ],
        'mid': [
            'How does Python manage memory and garbage collection?',
            'Explain list comprehensions and generator expressions.',
            'What is the difference between deep copy and shallow copy?',
        ],
        'senior': [
            'Explain Python\'s GIL and its impact on multithreading.',
            'How would you optimize a slow Python application?',
            'Explain metaclasses in Python.',
        ],
    },
    'django': {
        'junior': [
            'What is the Django MTV pattern?',
            'Explain Django models and migrations.',
            'What is the Django ORM?',
        ],
        'mid': [
            'What is the difference between select_related and prefetch_related?',
            'Explain Django middleware and how to write a custom one.',
            'How does Django handle authentication and permissions?',
        ],
        'senior': [
            'How would you scale a Django application to handle high traffic?',
            'Explain Django signals and when you would use them.',
            'How do you implement custom Django management commands?',
        ],
    },
    'react': {
        'junior': [
            'What is the difference between state and props in React?',
            'Explain what JSX is.',
            'What are React hooks?',
        ],
        'mid': [
            'Explain the React component lifecycle with hooks.',
            'What is the Context API and when would you use it?',
            'How does virtual DOM work in React?',
        ],
        'senior': [
            'How would you optimize a large React application\'s performance?',
            'Explain React\'s reconciliation algorithm.',
            'When would you use Redux over Context API?',
        ],
    },
    'javascript': {
        'junior': [
            'What is the difference between var, let, and const?',
            'Explain what a promise is in JavaScript.',
            'What is closure in JavaScript?',
        ],
        'mid': [
            'Explain the JavaScript event loop.',
            'What is event bubbling and event delegation?',
            'How does async/await work under the hood?',
        ],
        'senior': [
            'Explain JavaScript\'s prototype chain.',
            'How would you implement a debounce function?',
            'What are Web Workers and when would you use them?',
        ],
    },
    'sql': {
        'junior': [
            'What is the difference between INNER JOIN and LEFT JOIN?',
            'Explain what a primary key and foreign key are.',
            'What is the difference between WHERE and HAVING?',
        ],
        'mid': [
            'Explain database normalization and its forms.',
            'What are indexes and how do they improve performance?',
            'What is a subquery? Give an example.',
        ],
        'senior': [
            'How would you optimize a slow database query?',
            'Explain database transactions and ACID properties.',
            'What is query execution plan and how do you analyze it?',
        ],
    },
    'aws': {
        'junior': [
            'What is the difference between EC2 and Lambda?',
            'Explain what S3 is used for.',
            'What is IAM in AWS?',
        ],
        'mid': [
            'Explain S3 storage classes and when to use each.',
            'What is a VPC and why is it important?',
            'How does auto-scaling work in AWS?',
        ],
        'senior': [
            'Design a highly available architecture on AWS.',
            'Explain the difference between RDS Multi-AZ and Read Replicas.',
            'How would you implement a serverless architecture on AWS?',
        ],
    },
    'docker': {
        'junior': [
            'What is the difference between a Docker image and a container?',
            'What is a Dockerfile?',
            'What is Docker Compose?',
        ],
        'mid': [
            'Explain Docker volumes and networking.',
            'How do you optimize Docker image size?',
            'What is the difference between CMD and ENTRYPOINT?',
        ],
        'senior': [
            'How would you implement a CI/CD pipeline with Docker?',
            'Explain container orchestration and when to use Kubernetes vs Docker Swarm.',
            'How do you secure Docker containers in production?',
        ],
    },
    'machine learning': {
        'junior': [
            'What is the difference between supervised and unsupervised learning?',
            'Explain what a training set and test set are.',
            'What is overfitting?',
        ],
        'mid': [
            'Explain the bias-variance tradeoff.',
            'How does gradient descent work?',
            'What is cross-validation and why is it important?',
        ],
        'senior': [
            'How would you handle class imbalance in a dataset?',
            'Explain the attention mechanism in transformers.',
            'How would you deploy a machine learning model to production?',
        ],
    },
    'general': {
        'junior': [
            'Tell me about a project you built and what you learned from it.',
            'How do you approach debugging a problem?',
            'Where do you see yourself in 2 years?',
        ],
        'mid': [
            'Describe a challenging technical problem you solved.',
            'How do you stay up to date with new technologies?',
            'Tell me about a time you improved a process or system.',
        ],
        'senior': [
            'How do you mentor junior developers?',
            'Describe how you would architect a system from scratch.',
            'Tell me about a time you made a critical technical decision.',
        ],
    },
}


def get_level_key(experience_level):
    level = experience_level.lower()
    if any(x in level for x in ['junior', 'entry', 'fresher', '0', '1']):
        return 'junior'
    if any(x in level for x in ['senior', 'lead', 'principal', '5', '6', '7', '8']):
        return 'senior'
    return 'mid'


def generate_ai_questions(job_title, skills, experience_level, count=10):
    """Enhanced AI question generation with local intelligence"""
    level = get_level_key(experience_level)
    questions = []

    # Match skills to question banks
    matched_skills = [s.lower() for s in skills if s.lower() in QUESTION_BANK]
    for skill in matched_skills:
        qs = QUESTION_BANK[skill].get(level, QUESTION_BANK[skill]['mid'])
        questions.extend(qs[:2])
        if len(questions) >= count - 2:
            break

    # Add role-specific questions based on job title
    title_lower = job_title.lower()
    if 'frontend' in title_lower or 'react' in title_lower:
        questions.extend(QUESTION_BANK['react'].get(level, QUESTION_BANK['react']['mid'])[:2])
    elif 'backend' in title_lower or 'python' in title_lower:
        questions.extend(QUESTION_BANK['python'].get(level, QUESTION_BANK['python']['mid'])[:2])
    elif 'fullstack' in title_lower or 'full stack' in title_lower:
        questions.extend(QUESTION_BANK['javascript'].get(level, QUESTION_BANK['javascript']['mid'])[:1])
        questions.extend(QUESTION_BANK['python'].get(level, QUESTION_BANK['python']['mid'])[:1])
    elif 'data' in title_lower or 'ml' in title_lower or 'machine learning' in title_lower:
        questions.extend(QUESTION_BANK['machine learning'].get(level, QUESTION_BANK['machine learning']['mid'])[:2])
    elif 'devops' in title_lower or 'cloud' in title_lower:
        questions.extend(QUESTION_BANK['aws'].get(level, QUESTION_BANK['aws']['mid'])[:1])
        questions.extend(QUESTION_BANK['docker'].get(level, QUESTION_BANK['docker']['mid'])[:1])

    # Add general questions
    general_qs = QUESTION_BANK['general'].get(level, QUESTION_BANK['general']['mid'])
    for q in general_qs:
        if len(questions) >= count:
            break
        if q not in questions:
            questions.append(q)

    # Remove duplicates while preserving order
    seen = set()
    unique_questions = []
    for q in questions:
        if q not in seen:
            seen.add(q)
            unique_questions.append(q)

    return unique_questions[:count]


def calculate_job_match(candidate, job):
    """Enhanced job matching algorithm with better scoring"""
    candidate_skills = set(s.name.lower() for s in candidate.skills.all())
    job_skills_raw = [s.strip().lower() for s in job.skills_required.split(',') if s.strip()]
    job_skills = set(job_skills_raw)

    if not job_skills:
        return {'match_percentage': 0, 'matching_skills': [], 'missing_skills': []}

    # Exact matches
    exact_matches = list(candidate_skills & job_skills)
    
    # Fuzzy matches for similar skills
    fuzzy_matches = []
    skill_synonyms = {
        'javascript': ['js', 'node', 'nodejs'],
        'python': ['django', 'flask', 'fastapi'],
        'react': ['reactjs', 'react.js'],
        'aws': ['amazon web services', 'cloud'],
        'sql': ['mysql', 'postgresql', 'database'],
        'css': ['styling', 'sass', 'scss'],
        'html': ['markup', 'frontend'],
        'api': ['rest', 'restful', 'graphql'],
        'testing': ['jest', 'pytest', 'unit testing'],
        'git': ['version control', 'github', 'gitlab'],
    }
    
    for job_skill in job_skills - set(exact_matches):
        for candidate_skill in candidate_skills - set(exact_matches):
            # Check if skills are synonyms
            for primary, synonyms in skill_synonyms.items():
                if ((job_skill == primary and candidate_skill in synonyms) or 
                    (candidate_skill == primary and job_skill in synonyms) or
                    (job_skill in synonyms and candidate_skill in synonyms)):
                    if job_skill not in fuzzy_matches:
                        fuzzy_matches.append(job_skill)
                        break

    # Calculate match percentage (exact matches worth 100%, fuzzy matches worth 60%)
    total_matches = len(exact_matches) + (len(fuzzy_matches) * 0.6)
    percentage = round((total_matches / len(job_skills)) * 100, 1)
    
    # Boost percentage for high skill coverage
    if percentage > 70:
        percentage = min(percentage * 1.1, 95)  # Cap at 95%
    
    all_matching = exact_matches + [f"{skill} (similar)" for skill in fuzzy_matches]
    missing = list(job_skills - set(exact_matches) - set(fuzzy_matches))

    return {
        'match_percentage': min(percentage, 95),  # Cap at 95%
        'matching_skills': all_matching,
        'missing_skills': missing,
    }


def compute_experience_years(candidate):
    count = candidate.experience.count()
    return min(count * 1.5, 10)


def rank_candidates_for_job(job):
    applications = job.applications.select_related('candidate').all()
    scored = []

    for app in applications:
        candidate = app.candidate
        match_data = calculate_job_match(candidate, job)
        exp_years = compute_experience_years(candidate)
        cert_count = candidate.certifications.count() if hasattr(candidate, 'certifications') else 0

        match_score = match_data['match_percentage']
        exp_score = min(exp_years * 10, 100)
        cert_score = min(cert_count * 20, 100)
        total = round(match_score * 0.6 + exp_score * 0.3 + cert_score * 0.1, 1)

        JobMatch.objects.update_or_create(
            candidate=candidate, job=job,
            defaults={
                'match_percentage': match_score,
                'matching_skills': match_data['matching_skills'],
                'missing_skills': match_data['missing_skills'],
            }
        )

        scored.append({
            'candidate': candidate,
            'match_score': match_score,
            'experience_score': exp_score,
            'certification_score': cert_score,
            'total_score': total,
        })

    scored.sort(key=lambda x: x['total_score'], reverse=True)

    CandidateRanking.objects.filter(job=job).delete()
    rankings = []
    for i, item in enumerate(scored, 1):
        rankings.append(CandidateRanking(
            job=job,
            candidate=item['candidate'],
            rank=i,
            match_score=item['match_score'],
            experience_score=item['experience_score'],
            certification_score=item['certification_score'],
            total_score=item['total_score'],
        ))
    CandidateRanking.objects.bulk_create(rankings)
    return rankings


def sync_resume_analysis(candidate):
    skills = list(candidate.skills.values_list('name', flat=True))
    education = list(candidate.education.values('degree', 'institution', 'year'))
    experience = list(candidate.experience.values('title', 'company', 'duration'))
    certifications = list(candidate.certifications.values('name', 'issuer', 'year')) if hasattr(candidate, 'certifications') else []
    exp_years = compute_experience_years(candidate)

    # Compute ATS score
    score = 0
    if skills: score += min(len(skills) * 5, 30)
    if education: score += 20
    if experience: score += min(len(experience) * 10, 30)
    if certifications: score += min(len(certifications) * 5, 10)
    if candidate.resumes.filter(is_active=True).exists(): score += 10
    ats_score = min(score, 100)
    ats_confidence = min(ats_score + 5, 100)

    if ats_score >= 80:
        strength = 'Excellent'
    elif ats_score >= 60:
        strength = 'Good'
    elif ats_score >= 40:
        strength = 'Average'
    else:
        strength = 'Needs Improvement'

    ResumeAnalysis.objects.update_or_create(
        candidate=candidate,
        defaults={
            'skills': skills,
            'education': education,
            'experience': experience,
            'certifications': certifications,
            'experience_years': exp_years,
            'ats_score': ats_score,
            'ats_confidence': ats_confidence,
            'resume_strength': strength,
        }
    )
