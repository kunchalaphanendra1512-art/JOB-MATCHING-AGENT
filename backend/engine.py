import numpy as np

class MatchingEngine:
    def calculate_score(self, resume, job):
        # 1. Skill Match (40%)
        resume_skills = set([s.lower() for s in resume.skills])
        job_skills = [s.lower() for s in job.required_skills]
        overlap = len([s for s in job_skills if s in resume_skills])
        skill_score = (overlap / len(job_skills)) * 100 if job_skills else 100

        # 2. Experience (20%)
        exp_score = 100 if resume.experience_years >= job.required_experience else (resume.experience_years / job.required_experience) * 100

        # 3. Location (10%)
        loc_score = 100 if resume.location.lower() == job.location.lower() else 30

        # 4. Salary (10%)
        sal_score = 100 if job.salary_min <= resume.salary_expectation <= job.salary_max else 0

        # 5. Semantic (20%) - Simulated cosine similarity
        semantic_score = 85 # Placeholder for actual vector math

        final_score = (skill_score * 0.4) + (exp_score * 0.2) + (loc_score * 0.1) + (sal_score * 0.1) + (semantic_score * 0.2)

        return {
            "skill_score": skill_score,
            "experience_score": exp_score,
            "location_score": loc_score,
            "salary_score": sal_score,
            "semantic_score": semantic_score,
            "final_score": final_score
        }

class FraudDetector:
    def analyze(self, resume):
        trust_score = 100
        flags = []

        if len(resume.get('skills', [])) > 30:
            trust_score -= 10
            flags.append("Skill stuffing detected")
        
        if resume.get('experience_years', 0) > 50:
            trust_score -= 10
            flags.append("Unrealistic experience")

        return {
            "trust_score": trust_score,
            "flags": flags,
            "risk_level": "Low" if trust_score > 80 else "Medium" if trust_score > 60 else "High"
        }
