from typing import List, Dict

# Master Copilot Prompt scoring functions

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
    'ml': 'machine learning',
    'ai': 'artificial intelligence',
}


def normalize_skills(skills: List[str]) -> List[str]:
    """Lowercase, trim, remove duplicates, map synonyms."""
    normalized = []
    seen = set()
    for s in skills or []:
        if not s:
            continue
        n = s.lower().strip()
        n = SKILL_SYNONYMS.get(n, n)
        if n not in seen:
            seen.add(n)
            normalized.append(n)
    return normalized


def calculate_skill_score(resume_skills: List[str],
                          required_skills: List[str],
                          preferred_skills: List[str] = None) -> Dict:
    """Return dict with matched counts and score result."""
    req = normalize_skills(required_skills or [])
    pref = normalize_skills(preferred_skills or [])
    res = normalize_skills(resume_skills or [])

    total_required = len(req)
    matched_required = sum(1 for s in req if s in res)
    total_preferred = len(pref)
    matched_preferred = sum(1 for s in pref if s in res)

    skill_score = 0.0
    if total_required > 0:
        skill_score = (matched_required / total_required) * 70
    if total_preferred > 0:
        bonus = (matched_preferred / total_preferred) * 10
        skill_score += bonus
    skill_score = min(skill_score, 80)

    mismatch = total_required - matched_required

    return {
        'skill_score': skill_score,
        'matched_required': matched_required,
        'total_required': total_required,
        'matched_preferred': matched_preferred,
        'total_preferred': total_preferred,
        'skill_gaps': [s for s in req if s not in res][:3],
        'mismatch_pct': (mismatch / total_required * 100) if total_required > 0 else 0
    }


def calculate_experience_score(exp: int, min_exp: int) -> Dict:
    if min_exp <= 0:
        return {'experience_score': 15, 'meets': True}
    if exp >= min_exp:
        return {'experience_score': 15, 'meets': True}
    else:
        return {'experience_score': (exp / min_exp) * 15, 'meets': False}


def calculate_location_score(job_location: str, role_type: str, resume_location: str) -> Dict:
    # role_type may indicate remote/hybrid/onsite
    if 'remote' in role_type.lower():
        return {'location_score': 5, 'matches': True}
    if resume_location.lower().strip() == job_location.lower().strip():
        return {'location_score': 5, 'matches': True}
    return {'location_score': 0, 'matches': False}


def calculate_final_score(skill_score: float, experience_score: float, location_score: float,
                          matched_required: int, total_required: int, exp_meets: bool) -> float:
    score = skill_score + experience_score + location_score
    # allow 100 if all required matched and experience meets
    if total_required > 0 and matched_required == total_required and exp_meets:
        return 100.0
    return max(0, min(95, score))


def calculate_trust_score(matched_required: int, total_required: int,
                          exp_meets: bool, projects_count: int,
                          education: str) -> float:
    trust = 70
    if exp_meets:
        trust += 10
    if projects_count > 2:
        trust += 5
    if education and education.strip():
        trust += 5
    # skill consistency >60%
    if total_required > 0 and (matched_required / total_required) > 0.6:
        trust += 5
    # subtract if matched_required <50%
    if total_required > 0 and (matched_required / total_required) < 0.5:
        trust -= 10
    trust = max(50, min(95, trust))
    return trust


def calculate_risk_level(trust_score: float) -> str:
    if trust_score >= 85:
        return 'LOW'
    elif trust_score >= 70:
        return 'MEDIUM'
    else:
        return 'HIGH'
