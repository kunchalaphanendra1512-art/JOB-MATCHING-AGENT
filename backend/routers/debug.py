from fastapi import APIRouter
from backend.services.db import get_supabase

router = APIRouter()


@router.get("/supabase")
async def supabase_status():
    """Return whether the backend can access Supabase and a short error if not."""
    supabase = get_supabase()
    if supabase is None:
        return {"available": False, "error": "Supabase client not configured"}
    try:
        resp = supabase.table("jobs").select("id").limit(1).execute()
        if getattr(resp, "error", None):
            return {"available": False, "error": str(resp.error)}
        return {"available": True}
    except Exception as e:
        return {"available": False, "error": str(e)}
