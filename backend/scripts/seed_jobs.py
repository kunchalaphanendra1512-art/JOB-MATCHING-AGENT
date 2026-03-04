from backend.services.sqlite_db import insert_job_local
from datetime import datetime
import uuid

# A small collection of sample job postings with varied skills
sample_jobs = [
    {
        "title": "Senior Python Developer",
        "description": "Looking for a backend engineer experienced in Python, FastAPI, and PostgreSQL.",
        "required_skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
        "required_experience": 5,
        "location": "Remote",
        "salary_range_min": 120000,
        "salary_range_max": 150000,
        "poster_email": "recruiter1@example.com"
    },
    {
        "title": "Frontend Engineer (React)",
        "description": "Front‑end developer skilled in React, TypeScript, and modern CSS frameworks.",
        "required_skills": ["React", "TypeScript", "HTML", "CSS", "Tailwind"],
        "required_experience": 3,
        "location": "Remote",
        "salary_range_min": 90000,
        "salary_range_max": 110000,
        "poster_email": "recruiter2@example.com"
    },
    {
        "title": "DevOps Specialist",
        "description": "Engineer with hands‑on experience with Docker, Kubernetes, AWS, and CI/CD.",
        "required_skills": ["Docker", "Kubernetes", "AWS", "CI/CD"],
        "required_experience": 4,
        "location": "Remote",
        "salary_range_min": 110000,
        "salary_range_max": 140000,
        "poster_email": "recruiter3@example.com"
    },
    {
        "title": "Data Scientist",
        "description": "Data scientist familiar with Python, machine learning libraries and big data tools.",
        "required_skills": ["Python", "Machine Learning", "TensorFlow", "Spark"],
        "required_experience": 2,
        "location": "Remote",
        "salary_range_min": 100000,
        "salary_range_max": 130000,
        "poster_email": "recruiter4@example.com"
    }
]

for job in sample_jobs:
    record = {
        "id": str(uuid.uuid4()),
        "title": job["title"],
        "description": job.get("description"),
        "required_skills": job["required_skills"],
        "min_experience": job.get("required_experience"),
        "location": job.get("location", ""),
        # other salary fields are ignored in current schema
        "embedding": [],  # will be computed later if needed
        "poster_email": job.get("poster_email"),
        "role_type": job.get("role_type", "remote"),
        "created_at": datetime.utcnow().isoformat()
    }
    insert_job_local(record)
    print("Inserted local job", record["id"], "-", record["title"])

print("Seeding complete")
