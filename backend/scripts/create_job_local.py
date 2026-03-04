from backend.services.sqlite_db import insert_job_local
from datetime import datetime
import uuid

job = {
    "id": str(uuid.uuid4()),
    "title": "Test Job Offline",
    "description": "A sample job stored locally.",
    "required_skills": ["python"],
    "required_experience": 0,
    "location": "Remote",
    "salary_range_min": 0,
    "salary_range_max": 0,
    "embedding": [],
    "poster_email": "test@example.com",
    "created_at": datetime.utcnow().isoformat()
}

insert_job_local(job)
print("Inserted local job", job['id'])
