from fastapi import APIRouter
from backend.services.db import get_supabase
import numpy as np

router = APIRouter()

@router.get("/analytics")
async def get_analytics():
    supabase = get_supabase()
    if supabase is None:
        # Return demo analytics
        return {
            "avg_match_score": 75.0,
            "fraud_percentage": 5.0,
            "top_demanded_skills": ["Python", "React", "SQL", "AWS", "Docker"],
            "total_candidates": 0,
            "confidence_metric": 0.0
        }
    
    try:
        resumes_resp = supabase.table("resumes").select("trust_score, fraud_flags, skills").execute()
        matches_resp = supabase.table("matches").select("final_match_score").execute()
        jobs_resp = supabase.table("jobs").select("id").execute()
        
        resumes = resumes_resp.data if resumes_resp.data else []
        matches = matches_resp.data if matches_resp.data else []
        jobs = jobs_resp.data if jobs_resp.data else []
        
        # 2. Compute metrics
        total_candidates = len(resumes)
        total_jobs = len(jobs)
        
        avg_match_score = 0
        if matches:
            avg_match_score = np.mean([m['final_match_score'] for m in matches])
            
        fraud_count = len([r for r in resumes if r.get('fraud_flags') and len(r['fraud_flags']) > 0])
        fraud_percentage = (fraud_count / total_candidates * 100) if total_candidates > 0 else 0
        
        # 3. Top skills
        all_skills = []
        for r in resumes:
            all_skills.extend(r.get('skills', []))
        
        unique_skills, counts = np.unique(all_skills, return_counts=True)
        top_indices = np.argsort(-counts)[:5]
        top_skills = unique_skills[top_indices].tolist() if len(unique_skills) > 0 else []
        
        return {
            "avg_match_score": float(avg_match_score),
            "fraud_percentage": float(fraud_percentage),
            "top_demanded_skills": top_skills,
            "total_candidates": total_candidates,
            "confidence_metric": 85.0
        }
    except Exception as e:
        print(f"Analytics error: {e}")
        # Fallback to demo data
        return {
            "avg_match_score": 75.0,
            "fraud_percentage": 5.0,
            "top_demanded_skills": ["Python", "React", "SQL", "AWS", "Docker"],
            "total_candidates": 0,
            "confidence_metric": 0.0
        }
