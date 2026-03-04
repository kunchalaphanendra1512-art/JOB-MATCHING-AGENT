from typing import List


def generate_explanation(final_score: float, top_skills: List[str], gaps: List[str]) -> str:
    # build strings
    top = ', '.join(top_skills[:3]) if top_skills else ''
    gapstr = ', '.join(gaps[:3]) if gaps else 'none'

    if final_score >= 85:
        return f"The candidate strongly matches required skills including {top}. Minor gaps in {gapstr}. Experience meets expectations."
    elif final_score >= 60:
        return f"The candidate matches several core skills such as {top}, but lacks {gapstr}. Further review recommended."
    else:
        return f"The candidate does not sufficiently match required skills. Major gaps in {gapstr}."