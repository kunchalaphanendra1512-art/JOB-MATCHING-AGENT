from pydantic import BaseModel
from typing import List, Optional

class Resume(BaseModel):
    id: Optional[str] = None
    email: str
    skills: List[str]
    experience_years: int
    location: str
    salary_expectation: int
    summary: Optional[str] = None
    embedding: Optional[List[float]] = None

class Job(BaseModel):
    id: str
    title: str
    description: str
    required_skills: List[str]
    required_experience: int
    location: str
    salary_min: int
    salary_max: int
    embedding: Optional[List[float]] = None

class Match(BaseModel):
    resume_id: str
    job_id: str
    skill_score: float
    experience_score: float
    location_score: float
    salary_score: float
    semantic_score: float
    final_score: float
    explanation: str
    rank: int

class Analytics(BaseModel):
    avg_match_score: float
    fraud_percentage: float
    top_demanded_skills: List[str]
    total_candidates: int
    confidence_metric: float


# --- New models following Master Copilot Prompt spec ---

class JobCreate(BaseModel):
    title: str
    required_skills: List[str]
    preferred_skills: Optional[List[str]] = []
    min_experience: int
    location: str
    role_type: str  # remote/hybrid/onsite
    created_at: Optional[str] = None

class JobOut(JobCreate):
    id: str

class CandidateCreate(BaseModel):
    email: str
    skills: List[str]
    experience_years: int
    location: str
    education: Optional[str] = ""
    projects_count: int = 0
    created_at: Optional[str] = None

class CandidateOut(CandidateCreate):
    id: str

class MatchCreate(BaseModel):
    candidate_id: str
    job_id: str
    skill_score: float
    experience_score: float
    location_score: float
    final_score: float
    trust_score: float
    risk_level: str
    explanation: str
    created_at: Optional[str] = None

class MatchOut(MatchCreate):
    id: str
