QUESTION_BANK = {
    'python': [
        'Explain the difference between list and tuple in Python.',
        'What are Python decorators and how do you use them?',
        'How does Python manage memory? Explain garbage collection.',
        'What is the difference between deep copy and shallow copy?',
        'Explain list comprehensions with an example.',
    ],
    'django': [
        'Explain the Django request-response lifecycle.',
        'What is the difference between select_related and prefetch_related?',
        'How does Django ORM handle database migrations?',
        'Explain Django middleware and how to write a custom one.',
        'What are Django signals and when would you use them?',
    ],
    'javascript': [
        'Explain the difference between var, let and const.',
        'What is event bubbling and event delegation?',
        'How does the JavaScript event loop work?',
        'Explain promises and async/await.',
        'What is closure in JavaScript?',
    ],
    'react': [
        'What is the difference between state and props in React?',
        'Explain the React component lifecycle.',
        'What are React hooks? Explain useState and useEffect.',
        'How does virtual DOM work in React?',
        'What is the Context API and when would you use it?',
    ],
    'sql': [
        'What is the difference between INNER JOIN and LEFT JOIN?',
        'Explain database normalization and its forms.',
        'What are indexes and how do they improve performance?',
        'Explain the difference between WHERE and HAVING clauses.',
        'What is a subquery? Give an example.',
    ],
    'java': [
        'Explain the four pillars of OOP in Java.',
        'What is the difference between abstract class and interface?',
        'How does Java handle exceptions?',
        'Explain Java collections framework.',
        'What is multithreading and how is it implemented in Java?',
    ],
    'aws': [
        'What is the difference between EC2 and Lambda?',
        'Explain S3 storage classes.',
        'What is a VPC and why is it important?',
        'How does auto-scaling work in AWS?',
        'Explain the difference between RDS and DynamoDB.',
    ],
    'docker': [
        'What is the difference between a Docker image and a container?',
        'Explain Docker volumes and why they are used.',
        'What is Docker Compose and when would you use it?',
        'How do you optimize Docker image size?',
        'What is the difference between CMD and ENTRYPOINT?',
    ],
    'machine learning': [
        'Explain the bias-variance tradeoff.',
        'What is the difference between supervised and unsupervised learning?',
        'How does gradient descent work?',
        'Explain cross-validation and why it is important.',
        'What is overfitting and how do you prevent it?',
    ],
    'general': [
        'Tell me about yourself and your experience.',
        'What are your strengths and weaknesses?',
        'Describe a challenging project you worked on.',
        'Where do you see yourself in 5 years?',
        'Why do you want to work with us?',
    ],
}


def generate_questions(skills, count=8):
    questions = []
    matched_skills = [s.lower() for s in skills if s.lower() in QUESTION_BANK]

    for skill in matched_skills:
        questions.extend(QUESTION_BANK[skill][:2])
        if len(questions) >= count - 2:
            break

    # Fill remaining with general questions
    general = QUESTION_BANK['general']
    for q in general:
        if len(questions) >= count:
            break
        if q not in questions:
            questions.append(q)

    return questions[:count]
