"""
HireSense AI - Rule-Based Resume Matching Engine
Deterministic, explainable, no LLM-based scoring.
"""

class MatchingEngine:
    # Skill synonyms mapping for normalization
    SKILL_SYNONYMS = {
        'js': 'javascript',
        'ts': 'typescript',
        'py': 'python',
        'c++': 'cpp',
        'c#': 'csharp',
        'golang': 'go',
        'node': 'nodejs',
        'node.js': 'nodejs',
        'react.js': 'react',
        'angular.js': 'angular',
        'vue.js': 'vue',
        'sql': 'sql',
        'nosql': 'nosql',
        'ml': 'machine learning',
        'ai': 'artificial intelligence',
        'rest': 'rest api',
        'api': 'rest api',
    }

    @staticmethod
    def normalize_skill(skill: str) -> str:
        """Normalize skill name: lowercase, trim, apply synonyms."""
        normalized = skill.lower().strip()
        return MatchingEngine.SKILL_SYNONYMS.get(normalized, normalized)

    @staticmethod
    def normalize_skills(skills: list) -> set:
        """Normalize and deduplicate a list of skills."""
        return set(MatchingEngine.normalize_skill(s) for s in skills if s)

    @staticmethod
    def calculate_skill_match(resume_skills: list, required_skills: list, preferred_skills: list = None) -> dict:
        """
        Calculate skill match score (0-90%, never 100).
        
        Returns:
        {
            'matched_required': int,
            'matched_preferred': int,
            'total_required': int,
            'total_preferred': int,
            'skill_match_score': float (0-90),
            'matched_skills': list,
            'skill_gaps': list (top 3 unmatched required skills)
        }
        """
        if not required_skills:
            return {
                'matched_required': 0,
                'matched_preferred': 0,
                'total_required': 0,
                'total_preferred': 0,
                'skill_match_score': 0,
                'matched_skills': [],
                'skill_gaps': []
            }

        resume_norm = MatchingEngine.normalize_skills(resume_skills)
        required_norm = MatchingEngine.normalize_skills(required_skills)
        preferred_norm = MatchingEngine.normalize_skills(preferred_skills or [])

        # Core skill match
        matched_required = len(resume_norm.intersection(required_norm))
        skill_match_pct = (matched_required / len(required_norm)) * 100 if required_norm else 0

        # Preferred skills bonus (capped at 10%)
        matched_preferred = 0
        if preferred_norm:
            matched_preferred = len(resume_norm.intersection(preferred_norm))
            preferred_bonus = (matched_preferred / len(preferred_norm)) * 10
        else:
            preferred_bonus = 0

        # Core score (skill_match_pct + preferred_bonus), capped at 90
        skill_match_score = min(90, skill_match_pct + preferred_bonus)

        # Matched skills (for display)
        matched_skills = list(resume_norm.intersection(required_norm))[:5]

        # Skill gaps (top 3 unmatched required)
        gaps = list(required_norm - resume_norm)[:3]
        skill_gaps = gaps

        return {
            'matched_required': matched_required,
            'matched_preferred': matched_preferred,
            'total_required': len(required_norm),
            'total_preferred': len(preferred_norm),
            'skill_match_score': skill_match_score,
            'matched_skills': matched_skills,
            'skill_gaps': skill_gaps,
            'mismatch_count': len(required_norm) - matched_required
        }

    @staticmethod
    def calculate_experience_score(resume_experience: int, required_experience: int) -> dict:
        """
        Experience score (20 points max).
        If experience >= required: 20 points.
        Otherwise: (experience / required) * 20.
        """
        if required_experience <= 0:
            return {'experience_score': 20, 'meets_min': True}

        if resume_experience >= required_experience:
            return {'experience_score': 20, 'meets_min': True}
        else:
            score = (resume_experience / required_experience) * 20
            return {'experience_score': score, 'meets_min': False}

    @staticmethod
    def calculate_location_score(resume_location: str, job_location: str) -> dict:
        """
        Location score (5 points max).
        - Remote job: 5 points (always)
        - Exact match: 5 points
        - Otherwise: 0 points
        """
        if not job_location:
            return {'location_score': 5, 'matches': True}

        job_loc_lower = job_location.lower().strip()
        resume_loc_lower = resume_location.lower().strip() if resume_location else ""

        # Check if job is remote
        if 'remote' in job_loc_lower:
            return {'location_score': 5, 'matches': True}

        # Exact match
        if resume_loc_lower == job_loc_lower:
            return {'location_score': 5, 'matches': True}

        return {'location_score': 0, 'matches': False}

    @staticmethod
    def calculate_trust_score(resume: dict, matched_skills_count: int, total_required_skills: int, experience_meets: bool, skill_gaps_count: int) -> dict:
        """
        Trust Score (confidence in verification): 50-95.
        
        Start: 70
        +10 if experience >= required
        +5 if education provided
        +5 if projects > 2
        +5 if skill consistency (matched > 50% of required)
        -10 if missing core data
        -5 if mismatch > 40%
        
        Clamp: 50-95
        """
        trust_score = 70

        # Check if has education
        education = resume.get('education') or []
        if education and len(education) > 0:
            trust_score += 5

        # Check if has projects
        projects = resume.get('projects') or []
        if projects and len(projects) > 2:
            trust_score += 5

        # Experience met
        if experience_meets:
            trust_score += 10

        # Skill consistency
        if total_required_skills > 0:
            match_ratio = matched_skills_count / total_required_skills
            if match_ratio > 0.5:
                trust_score += 5

        # Penalize missing core data
        if not resume.get('skills') or len(resume.get('skills', [])) == 0:
            trust_score -= 10
        if not resume.get('experience_years'):
            trust_score -= 10

        # Penalize high mismatch
        mismatch_pct = (skill_gaps_count / total_required_skills * 100) if total_required_skills > 0 else 0
        if mismatch_pct > 40:
            trust_score -= 5

        # Clamp to 50-95
        trust_score = max(50, min(95, trust_score))

        return {'trust_score': trust_score}

    @staticmethod
    def calculate_risk_level(trust_score: int) -> dict:
        """
        Risk Level:
        >= 85: LOW
        >= 70: MEDIUM
        < 70: HIGH
        """
        if trust_score >= 85:
            risk = "LOW"
        elif trust_score >= 70:
            risk = "MEDIUM"
        else:
            risk = "HIGH"

        return {'risk_level': risk}

    @staticmethod
    def generate_explanation(skill_match_score: float, matched_skills: list, skill_gaps: list, experience_meets: bool, trust_score: int) -> str:
        """
        Template-based explanation engine.
        No free text generation.
        """
        if not matched_skills or len(matched_skills) == 0:
            return "The candidate does not sufficiently match required skills. Major gaps identified. Profile may not be suitable."

        top_skills = ', '.join(matched_skills[:3])
        top_gaps = ', '.join(skill_gaps[:3]) if skill_gaps else "None"

        if skill_match_score >= 75:
            # Strong match
            exp_status = "meets" if experience_meets else "partially meets"
            if skill_gaps:
                return f"The candidate demonstrates strong alignment with required skills including {top_skills}. Experience {exp_status} requirements. Minor gaps exist in {top_gaps}. Overall profile suitability is high."
            else:
                return f"The candidate demonstrates strong alignment with all required skills including {top_skills}. Experience {exp_status} requirements. Overall profile suitability is excellent."

        elif skill_match_score >= 50:
            # Moderate match
            return f"The candidate meets several core requirements such as {top_skills}, but lacks experience in {top_gaps}. Further evaluation recommended."

        else:
            # Weak match
            return f"The candidate does not sufficiently match required skills. Major gaps identified in {top_gaps}. Profile may not be suitable."

    @staticmethod
    def calculate_final_score(skill_match_score: float, experience_score: float, location_score: float) -> float:
        """
        Final Match Score (0-95, never 100 unless all perfect).
        
        Formula:
        final_score = (skill_match_score * 0.7) + experience_score + location_score
        
        Clamp: 0-95
        """
        final_score = (skill_match_score * 0.7) + experience_score + location_score
        return max(0, min(95, final_score))

    def calculate_score(self, resume: dict, job: dict) -> dict:
        """
        Master method: Calculate complete match score with all components.
        
        Returns comprehensive match object with:
        - final_match_score (0-95)
        - skill_score, experience_score, location_score
        - matched_skills, skill_gaps
        - trust_score (50-95)
        - risk_level (LOW/MEDIUM/HIGH)
        - explanation (template-based)
        - match_grade (Excellent/Strong/Moderate/Weak/Poor)
        """

        # Edge case: no skills extracted
        if not resume.get('skills') or len(resume.get('skills', [])) == 0:
            return {
                'skill_score': 0,
                'experience_score': 0,
                'location_score': 0,
                'final_match_score': 0,
                'matched_skills': [],
                'skill_gaps': job.get('required_skills', [])[:3],
                'trust_score': 50,
                'risk_level': 'HIGH',
                'explanation': 'Insufficient resume data. Profile cannot be evaluated.',
                'match_grade': 'Poor Fit',
                'mismatch_pct': 100
            }

        # 1. Skill Match
        skill_result = self.calculate_skill_match(
            resume.get('skills', []),
            job.get('required_skills', []),
            job.get('preferred_skills', [])
        )
        skill_match_score = skill_result['skill_match_score']
        matched_skills = skill_result['matched_skills']
        skill_gaps = skill_result['skill_gaps']

        # 2. Experience
        # job postings may use either 'required_experience' or 'min_experience'
        req_exp = job.get('required_experience')
        if req_exp is None:
            req_exp = job.get('min_experience', 0)
        exp_result = self.calculate_experience_score(
            resume.get('experience_years', 0),
            req_exp or 0
        )
        experience_score = exp_result['experience_score']
        experience_meets = exp_result['meets_min']

        # 3. Location
        loc_result = self.calculate_location_score(
            resume.get('location', ''),
            job.get('location', '')
        )
        location_score = loc_result['location_score']

        # 4. Final Score
        final_match_score = self.calculate_final_score(
            skill_match_score,
            experience_score,
            location_score
        )

        # 5. Trust Score
        trust_result = self.calculate_trust_score(
            resume,
            skill_result['matched_required'],
            skill_result['total_required'],
            experience_meets,
            skill_result['mismatch_count']
        )
        trust_score = trust_result['trust_score']

        # 6. Risk Level
        risk_result = self.calculate_risk_level(trust_score)
        risk_level = risk_result['risk_level']

        # 7. Explanation
        explanation = self.generate_explanation(
            skill_match_score,
            matched_skills,
            skill_gaps,
            experience_meets,
            trust_score
        )

        # 8. Match Grade (for UI categorization)
        if final_match_score >= 90:
            match_grade = 'Excellent Match'
        elif final_match_score >= 75:
            match_grade = 'Strong Match'
        elif final_match_score >= 60:
            match_grade = 'Moderate Match'
        elif final_match_score >= 40:
            match_grade = 'Weak Match'
        else:
            match_grade = 'Poor Fit'

        # 9. Mismatch percentage
        mismatch_pct = (skill_result['mismatch_count'] / skill_result['total_required'] * 100) if skill_result['total_required'] > 0 else 0

        return {
            'skill_score': round(skill_match_score, 1),
            'experience_score': round(experience_score, 1),
            'location_score': round(location_score, 1),
            'final_match_score': round(final_match_score, 1),
            'matched_skills': matched_skills,
            'skill_gaps': skill_gaps,
            'trust_score': round(trust_score, 1),
            'risk_level': risk_level,
            'explanation': explanation,
            'match_grade': match_grade,
            'mismatch_pct': round(mismatch_pct, 1)
        }
