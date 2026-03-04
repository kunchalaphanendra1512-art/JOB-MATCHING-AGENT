import os
import re
import json
from typing import List, Dict
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

app = FastAPI(title="HireSense AI Engine")

# --- Models ---

class Resume(BaseModel):
    id: str
    skills: List[str]
    experience_years: int
    location: str
    salary_expectation: int
    embedding: List[float]
    extracted_text: str

class Job(BaseModel):
    id: str
    required_skills: List[str]
    required_experience: int
    location: str
    salary_range: Dict[str, int] # {"min": 50000, "max": 100000}
    embedding: List[float]

# --- ML Logic ---

class MatchingEngine:
    @staticmethod
    def calculate_skill_score(resume_skills: List[str], job_skills: List[str]) -> float:
        if not job_skills: return 100.0
        intersection = set(resume_skills).intersection(set(job_skills))
        return (len(intersection) / len(job_skills)) * 100

    @staticmethod
    def calculate_experience_score(candidate_exp: int, required_exp: int) -> float:
        if candidate_exp >= required_exp:
            return 100.0
        return (candidate_exp / required_exp) * 100 if required_exp > 0 else 100.0

    @staticmethod
    def calculate_location_score(candidate_loc: str, job_loc: str) -> float:
        if candidate_loc.lower() == job_loc.lower():
            return 100.0
        # Simple heuristic: same state check (mocked here)
        if "," in candidate_loc and "," in job_loc:
            if candidate_loc.split(",")[-1].strip() == job_loc.split(",")[-1].strip():
                return 70.0
        return 30.0

    @staticmethod
    def calculate_salary_score(expectation: int, salary_range: Dict[str, int]) -> float:
        if salary_range["min"] <= expectation <= salary_range["max"]:
            return 100.0
        return 0.0

    @staticmethod
    def calculate_semantic_score(resume_emb: List[float], job_emb: List[float]) -> float:
        res = np.array(resume_emb).reshape(1, -1)
        job = np.array(job_emb).reshape(1, -1)
        return float(cosine_similarity(res, job)[0][0]) * 100

    def match(self, resume: Resume, job: Job) -> Dict:
        skill_s = self.calculate_skill_score(resume.skills, job.required_skills)
        exp_s = self.calculate_experience_score(resume.experience_years, job.required_experience)
        loc_s = self.calculate_location_score(resume.location, job.location)
        sal_s = self.calculate_salary_score(resume.salary_expectation, job.salary_range)
        sem_s = self.calculate_semantic_score(resume.embedding, job.embedding)

        # FINAL MATCH SCORE FORMULA:
        # Skill Match Score (40%)
        # Experience Score (20%)
        # Location Compatibility (10%)
        # Salary Compatibility (10%)
        # Semantic Similarity (20%)
        
        final_score = (
            (skill_s * 0.4) +
            (exp_s * 0.2) +
            (loc_s * 0.1) +
            (sal_s * 0.1) +
            (sem_s * 0.2)
        )

        return {
            "skill_score": skill_s,
            "experience_score": exp_s,
            "location_score": loc_s,
            "salary_score": sal_s,
            "semantic_score": sem_s,
            "final_match_score": final_score,
            "explanation": f"Matched {len(set(resume.skills).intersection(job.required_skills))} skills. Experience is {'sufficient' if exp_s == 100 else 'below requirement'}."
        }

# --- Fraud Detection ---

class FraudDetector:
    @staticmethod
    def detect_fraud(resume: Resume, all_resumes: List[Resume]) -> Dict:
        trust_score = 100
        flags = []

        # 1. Duplicate detection (Similarity > 90%)
        for other in all_resumes:
            if other.id == resume.id: continue
            sim = float(cosine_similarity(np.array(resume.embedding).reshape(1,-1), np.array(other.embedding).reshape(1,-1))[0][0])
            if sim > 0.90:
                trust_score -= 20
                flags.append("Duplicate profile detected")
                break

        # 2. Skill stuffing (> 30 skills)
        if len(resume.skills) > 30:
            trust_score -= 10
            flags.append("Skill stuffing detected (>30 skills)")

        # 3. Contact validation (Simple Regex)
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.search(email_pattern, resume.extracted_text):
            trust_score -= 5
            flags.append("Invalid contact format")

        # 4. Unrealistic experience (Mocked logic)
        if resume.experience_years > 50:
            trust_score -= 10
            flags.append("Unrealistic experience timeline")

        return {
            "trust_score": max(0, trust_score),
            "fraud_flags": flags
        }

# --- API Endpoints ---

engine = MatchingEngine()
detector = FraudDetector()

@app.post("/match")
async def get_match(resume: Resume, job: Job):
    return engine.match(resume, job)

@app.post("/validate")
async def validate_resume(resume: Resume, all_resumes: List[Resume]):
    return detector.detect_fraud(resume, all_resumes)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
