from fastapi import APIRouter, HTTPException
from typing import List
from backend.services.db import get_supabase
from backend.models import CandidateCreate, CandidateOut
from datetime import datetime

router = APIRouter()

# offline cache when Supabase not available
OFFLINE_CANDIDATES: List[dict] = []

@router.post("/candidates", response_model=CandidateOut)
async def create_candidate(candidate: CandidateCreate):
    supabase = get_supabase()
    candidate.created_at = datetime.utcnow().isoformat()
    if supabase is None:
        fake = candidate.dict()
        fake['id'] = f"local-{int(datetime.utcnow().timestamp())}"
        OFFLINE_CANDIDATES.append(fake)
        return fake
    resp = supabase.table("candidates").insert(candidate.dict()).execute()
    if resp.error:
        raise HTTPException(status_code=500, detail=str(resp.error))
    return resp.data[0]

@router.get("/candidates", response_model=List[CandidateOut])
async def list_candidates():
    supabase = get_supabase()
    if supabase is None:
        return OFFLINE_CANDIDATES
    try:
        resp = supabase.table("candidates").select("*").order("created_at", desc=True).execute()
        return resp.data or []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
