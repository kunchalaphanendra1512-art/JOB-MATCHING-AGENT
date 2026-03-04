import os
import sqlite3
import json
from typing import Any, Dict, List

# location relative to project root
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "hiresense.db")
_conn: sqlite3.Connection = None


def get_sqlite_conn() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        _conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _init_schema(_conn)
    return _conn


def _init_schema(conn: sqlite3.Connection):
    c = conn.cursor()
    # jobs table
    c.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        id TEXT PRIMARY KEY,
        title TEXT,
        description TEXT,
        required_skills TEXT,
        required_experience INTEGER,
        location TEXT,
        salary_range_min INTEGER,
        salary_range_max INTEGER,
        embedding TEXT,
        poster_email TEXT,
        created_at TEXT
    )
    """)
    # resumes table
    c.execute("""
    CREATE TABLE IF NOT EXISTS resumes (
        id TEXT PRIMARY KEY,
        email TEXT,
        skills TEXT,
        experience_years INTEGER,
        location TEXT,
        salary_expectation INTEGER,
        summary TEXT,
        trust_score INTEGER,
        fraud_flags TEXT,
        risk_level TEXT,
        embedding TEXT,
        extracted_text TEXT
    )
    """)
    # matches table
    c.execute("""
    CREATE TABLE IF NOT EXISTS matches (
        id TEXT PRIMARY KEY,
        resume_id TEXT,
        job_id TEXT,
        skill_score REAL,
        experience_score REAL,
        location_score REAL,
        salary_score REAL,
        semantic_score REAL,
        final_match_score REAL,
        explanation TEXT
    )
    """)
    conn.commit()


def insert_job_local(job: Dict[str, Any]):
    conn = get_sqlite_conn()
    c = conn.cursor()
    # convert skills/embedding to JSON string
    skills = json.dumps(job.get('required_skills', []))
    embedding = json.dumps(job.get('embedding', []))
    c.execute(
        """INSERT OR REPLACE INTO jobs (id,title,description,required_skills,required_experience,location,salary_range_min,salary_range_max,embedding,poster_email,created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (
            job.get('id'),
            job.get('title'),
            job.get('description'),
            skills,
            job.get('required_experience'),
            job.get('location'),
            job.get('salary_range_min'),
            job.get('salary_range_max'),
            embedding,
            job.get('poster_email'),
            job.get('created_at'),
        ),
    )
    conn.commit()


def get_all_jobs_local() -> List[Dict[str, Any]]:
    conn = get_sqlite_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM jobs ORDER BY created_at DESC")
    rows = c.fetchall()
    jobs: List[Dict[str, Any]] = []
    for r in rows:
        j = dict(r)
        # normalize field names to match JobCreate/JobOut expectations
        # older records may have required_experience instead of min_experience
        if 'min_experience' not in j and 'required_experience' in j:
            j['min_experience'] = j.get('required_experience', 0) or 0
        # jobs created via old seed may not have a role_type, default to remote
        if 'role_type' not in j:
            j['role_type'] = 'remote'
        # preferred_skills wasn't stored before
        if 'preferred_skills' not in j:
            j['preferred_skills'] = []
        # convert skills/embedding json strings
        try:
            j['required_skills'] = json.loads(j.get('required_skills', '[]'))
        except Exception:
            j['required_skills'] = []
        try:
            j['embedding'] = json.loads(j.get('embedding', '[]'))
        except Exception:
            j['embedding'] = []
        jobs.append(j)
    return jobs
