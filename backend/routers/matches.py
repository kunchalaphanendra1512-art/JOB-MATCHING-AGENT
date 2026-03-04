from fastapi import APIRouter, HTTPException
from backend.services.db import get_supabase
from backend.models import MatchCreate, MatchOut
from backend.scoring import normalize_skills, calculate_skill_score, calculate_experience_score, calculate_location_score, calculate_final_score, calculate_trust_score, calculate_risk_level
from backend.explanation import generate_explanation
from backend.ranking import rank_matches
from datetime import datetime
from typing import List

router = APIRouter()

# simple in-memory caches when Supabase is unavailable
OFFLINE_MATCHES: List[dict] = []

@router.post("/match/{candidate_id}/{job_id}", response_model=MatchOut)
async def create_match(candidate_id: str, job_id: str):
    supabase = get_supabase()

    candidate = None
    job = None
    if supabase:
        # fetch candidate
        try:
            cand_resp = supabase.table("candidates").select("*").eq("id", candidate_id).single().execute()
            candidate = cand_resp.data
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to fetch candidate: {e}")
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")

        # fetch job
        try:
            job_resp = supabase.table("jobs").select("*").eq("id", job_id).single().execute()
            job = job_resp.data
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to fetch job: {e}")
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
    else:
        # no database - create fake candidate and job based on defaults
        candidate = {
            "id": candidate_id,
            "email": "offline@example.com",
            "skills": ["python"],
            "experience_years": 1,
            "location": "Remote",
            "education": "",
            "projects_count": 0
        }
        job = {
            "id": job_id,
            "required_skills": ["python"],
            "preferred_skills": [],
            "min_experience": 0,
            "location": "Remote",
            "role_type": "remote"
        }

    # scoring
    skill_data = calculate_skill_score(candidate.get("skills", []), job.get("required_skills", []), job.get("preferred_skills", []))
    exp_data = calculate_experience_score(candidate.get("experience_years", 0), job.get("min_experience", 0))
    loc_data = calculate_location_score(job.get("location", ""), job.get("role_type", ""), candidate.get("location", ""))

    final_score = calculate_final_score(skill_data['skill_score'], exp_data['experience_score'], loc_data['location_score'], skill_data['matched_required'], skill_data['total_required'], exp_data['meets'])
    trust_score = calculate_trust_score(skill_data['matched_required'], skill_data['total_required'], exp_data['meets'], candidate.get('projects_count', 0), candidate.get('education', ''))
    risk_level = calculate_risk_level(trust_score)
    explanation = generate_explanation(final_score, skill_data.get('skill_gaps', []), skill_data.get('skill_gaps', []))

    match_obj = {
        "candidate_id": candidate_id,
        "job_id": job_id,
        "skill_score": skill_data['skill_score'],
        "experience_score": exp_data['experience_score'],
        "location_score": loc_data['location_score'],
        "final_score": final_score,
        "trust_score": trust_score,
        "risk_level": risk_level,
        "explanation": explanation,
        "created_at": datetime.utcnow().isoformat()
    }

    # persist if possible, otherwise return fake
    if supabase:
        try:
            resp = supabase.table("matches").insert(match_obj).execute()
            if resp.error:
                raise HTTPException(status_code=500, detail=str(resp.error))
            return resp.data[0]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save match: {e}")
    else:
        fake = match_obj.copy()
        fake['id'] = f"local-{int(datetime.utcnow().timestamp())}"
        OFFLINE_MATCHES.append(fake)
        return fake

@router.get("/ranked/{job_id}", response_model=List[MatchOut])
async def get_ranked(job_id: str):
    supabase = get_supabase()
    if supabase is None:
        # return any offline matches for this job
        return [m for m in OFFLINE_MATCHES if m.get('job_id') == job_id]
    try:
        resp = supabase.table("matches").select("*").eq("job_id", job_id).execute()
        matches = resp.data or []
        # ranking may depend on candidate experience; fetch candidates map
        cand_ids = [m['candidate_id'] for m in matches]
        cand_map = {}
        if cand_ids:
            cand_resp = supabase.table("candidates").select("id,experience_years").in_('id', cand_ids).execute()
            for c in cand_resp.data or []:
                cand_map[c['id']] = c
        for m in matches:
            if 'experience_years' not in m:
                m['experience_years'] = cand_map.get(m['candidate_id'], {}).get('experience_years', 0)
        ranked = rank_matches(matches)
        return ranked
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

