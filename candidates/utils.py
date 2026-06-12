import re
import fitz  # PyMuPDF
from docx import Document


def extract_text(file_path):
    if file_path.endswith('.pdf'):
        doc = fitz.open(file_path)
        return "\n".join(page.get_text() for page in doc)
    elif file_path.endswith('.docx'):
        doc = Document(file_path)
        return "\n".join(p.text for p in doc.paragraphs)
    return ""


SKILL_KEYWORDS = [
    'python', 'java', 'javascript', 'react', 'django', 'node', 'sql', 'mongodb',
    'aws', 'docker', 'kubernetes', 'git', 'html', 'css', 'typescript', 'c++',
    'machine learning', 'deep learning', 'tensorflow', 'pytorch', 'flask', 'fastapi',
    'c', 'data structure', 'figma', 'ui ux', 'data analytics',
]

DEGREE_KEYWORDS = ['bachelor', 'master', 'b.sc', 'm.sc', 'b.tech', 'm.tech', 'phd', 'mba', 'b.e', 'm.e', 'b.voc', 'vocational']

CERT_KEYWORDS = ['certified', 'certification', 'certificate', 'aws certified', 'pmp', 'cisco', 'comptia', 'google certified', 'microsoft certified']


def extract_skills(text):
    text_lower = text.lower()
    return list({skill for skill in SKILL_KEYWORDS if skill in text_lower})


def extract_education(text):
    education = []
    lines = text.split('\n')
    for i, line in enumerate(lines):
        line_lower = line.lower()
        if any(deg in line_lower for deg in DEGREE_KEYWORDS):
            degree = line.strip()
            institution = lines[i + 1].strip() if i + 1 < len(lines) else ''
            year_match = re.search(r'\b(19|20)\d{2}\b', line + (lines[i+1] if i+1 < len(lines) else ''))
            education.append({
                'degree': degree[:200],
                'institution': institution[:200],
                'year': year_match.group() if year_match else ''
            })
    return education[:5]


def extract_experience(text):
    experience = []
    lines = text.split('\n')
    job_pattern = re.compile(r'(engineer|developer|analyst|manager|internship|designer|consultant|lead)', re.IGNORECASE)
    for i, line in enumerate(lines):
        if job_pattern.search(line) and len(line.strip()) > 5:
            title = line.strip()
            company = lines[i + 1].strip() if i + 1 < len(lines) else ''
            duration_match = re.search(r'(\d{4})\s*[-–]\s*(\d{4}|present)', text[max(0, text.find(line)-50):text.find(line)+200], re.IGNORECASE)
            experience.append({
                'title': title[:200],
                'company': company[:200],
                'duration': duration_match.group() if duration_match else '',
                'description': ''
            })
    return experience[:5]


def extract_certifications(text):
    certifications = []
    text_lower = text.lower()
    lines = text.split('\n')
    for i, line in enumerate(lines):
        line_lower = line.lower()
        if any(kw in line_lower for kw in CERT_KEYWORDS) and len(line.strip()) > 5:
            year_match = re.search(r'\b(19|20)\d{2}\b', line)
            certifications.append({
                'name': line.strip()[:200],
                'issuer': '',
                'year': year_match.group() if year_match else ''
            })
    return certifications[:5]


def parse_resume(file_path):
    text = extract_text(file_path)
    return {
        'skills': extract_skills(text),
        'education': extract_education(text),
        'experience': extract_experience(text),
        'certifications': extract_certifications(text),
    }
