from fastapi import APIRouter, HTTPException
from typing import List, Optional
from backend.services.db import get_supabase
from backend.models import JobCreate, JobOut
from backend.services.sqlite_db import insert_job_local, get_all_jobs_local
from datetime import datetime

router = APIRouter()

# offline cache when Supabase not available (temporary in-memory, mostly for very rapid failures)
OFFLINE_JOBS: List[dict] = []

@router.post("/jobs", response_model=JobOut)
async def create_job(job: JobCreate):
    supabase = get_supabase()
    job.created_at = datetime.utcnow().isoformat()

    # always persist in local SQLite for reliability
    local = job.dict()
    if not local.get('id'):
        local['id'] = f"local-{int(datetime.utcnow().timestamp())}"
    insert_job_local(local)

    # if supabase exists, attempt to store there too (but ignore errors)
    if supabase is None:
        fake = local.copy()
        OFFLINE_JOBS.append(fake)
        return fake
    try:
        resp = supabase.table("jobs").insert(job.dict()).execute()
        # log response for debugging
        print("Supabase insert resp:", getattr(resp, '__dict__', resp))
        if getattr(resp, 'error', None):
            err = str(resp.error)
            print("Supabase returned error:", err)
            # if schema cache issue, fall back to raw SQL RPC
            if 'schema cache' in err or 'could not find' in err.lower():
                query = (
                    "INSERT INTO jobs "
                    "(title, required_skills, preferred_skills, min_experience, location, role_type, created_at) "
                    f"VALUES ('{job.title}', '{{{','.join(job.required_skills)}}}', '{{{','.join(job.preferred_skills)}}}', {job.min_experience}, '{job.location}', '{job.role_type}', '{job.created_at}') "
                    "RETURNING *;"
                )
                print("Attempting RPC fallback with query", query)
                rpc_resp = supabase.rpc('sql', {'query': query}).execute()
                print("RPC resp", getattr(rpc_resp, '__dict__', rpc_resp))
                # supabase-py returns .data for RPC maybe
                return rpc_resp.data if getattr(rpc_resp, 'data', None) else local
            raise HTTPException(status_code=500, detail=err)
        # ensure data exists
        data = resp.data[0] if getattr(resp, 'data', None) else None
        if not data:
            # if supabase returned no data, just return local copy
            return local
        return data
    except HTTPException:
        raise
    except Exception as e:
        # network/timeout -> return local
        print("Supabase operation failed, using local job:", e)
        return local

@router.get("/jobs", response_model=List[JobOut])
async def list_jobs():
    # always return local jobs immediately - remote fetch is optional and can hang
    local_jobs = get_all_jobs_local()

    supabase = get_supabase()
    if supabase is None:
        return local_jobs
    # perform a non-blocking supabase fetch so UI can still use local data quickly
    # (we deliberately do not await or return the remote data here)
    def _sync_remote():
        try:
            resp = supabase.table("jobs").select("*").order("created_at", desc=True).execute()
            if resp.data:
                # optionally merge or log
                print("[jobs] fetched remote jobs count", len(resp.data))
        except Exception as e:
            print("Error fetching from Supabase (ignored):", e)
    import threading
    threading.Thread(target=_sync_remote, daemon=True).start()

    return local_jobs


from pydantic import BaseModel
from typing import Optional

class JobPost(BaseModel):
    """Frontend-format job posting — sent by App.tsx handleCreateJob."""
    title: str
    description: Optional[str] = ""
    required_skills: list
    required_experience: int = 0
    location: str
    salary_min: Optional[int] = 0
    salary_max: Optional[int] = 0
    poster_email: Optional[str] = ""

@router.post("/post-job")
async def post_job(job: JobPost):
    """Alias for the frontend's /api/post-job call.
    Maps the frontend job format to the backend DB format and saves it.
    """
    supabase = get_supabase()
    now = datetime.utcnow().isoformat()
    local_id = f"local-{int(datetime.utcnow().timestamp())}"

    job_data = {
        "id": local_id,
        "title": job.title,
        "description": job.description,
        "required_skills": job.required_skills,
        "preferred_skills": [],
        "min_experience": job.required_experience,
        "required_experience": job.required_experience,
        "location": job.location,
        "role_type": "onsite",
        "salary_min": job.salary_min,
        "salary_max": job.salary_max,
        "poster_email": job.poster_email,
        "created_at": now,
    }

    # Save to local SQLite
    insert_job_local(job_data)

    # Try Supabase
    if supabase is not None:
        try:
            resp = supabase.table("jobs").insert(job_data).execute()
            if resp.data:
                return resp.data[0]
        except Exception as e:
            print(f"Supabase post-job error (using local): {e}")

    return job_data
