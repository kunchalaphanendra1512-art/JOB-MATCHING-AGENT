import numpy as np
import re
from sklearn.metrics.pairwise import cosine_similarity

class FraudDetector:
    def analyze(self, resume: dict, all_resumes: list) -> dict:
        """
        Analyzes a resume for potential fraud and calculates a trust score.
        """
        trust_score = 100
        flags = []

        # 1. Duplicate detection (Similarity > 0.90)
        res_emb = np.array(resume.get('embedding', [])).reshape(1, -1)
        for other in all_resumes:
            if other.get('id') == resume.get('id'):
                continue
            
            other_emb = np.array(other.get('embedding', [])).reshape(1, -1)
            if res_emb.size > 0 and other_emb.size > 0:
                similarity = cosine_similarity(res_emb, other_emb)[0][0]
                if similarity > 0.90:
                    trust_score -= 20
                    flags.append("Duplicate profile detected (High similarity to existing record)")
                    break

        # 2. Skill stuffing (> 30 skills)
        if len(resume.get('skills', [])) > 30:
            trust_score -= 10
            flags.append("Skill stuffing detected (>30 skills)")

        # 3. Invalid email format
        email = resume.get('email', '')
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            trust_score -= 5
            flags.append("Invalid email format")

        # 4. Unrealistic experience timeline
        exp = resume.get('experience_years', 0)
        if exp > 50:
            trust_score -= 10
            flags.append("Unrealistic experience timeline (>50 years)")

        # 5. Duplicate email check
        for other in all_resumes:
            if other.get('email') == email and other.get('id') != resume.get('id'):
                trust_score -= 15
                flags.append("Duplicate email address in database")
                break

        trust_score = max(0, trust_score)
        risk_level = "Low" if trust_score > 80 else "Medium" if trust_score > 60 else "High"

        return {
            "trust_score": trust_score,
            "fraud_flags": flags,
            "risk_level": risk_level
        }
