from typing import List, Dict


def rank_matches(matches: List[Dict]) -> List[Dict]:
    # matches expected to include final_score, trust_score, and resume.experience_years perhaps
    return sorted(
        matches,
        key=lambda m: (
            -m.get('final_score', 0),
            -m.get('trust_score', 0),
            -((m.get('experience_years') or m.get('resume', {}).get('experience_years', 0)) or 0)
        )
    )
