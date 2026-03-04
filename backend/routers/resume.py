from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from backend.services.resume_parser import ResumeParser
from backend.services.embedding_service import EmbeddingService
from backend.services.fraud_detection import FraudDetector
from backend.services.matching_engine import MatchingEngine
from backend.services.db import get_supabase
from backend.services.analysis_service import AnalysisService
from datetime import datetime
import json

router = APIRouter()

@router.post("/upload-resume")
async def upload_resume(
    file: UploadFile = File(...),
    location: str = Form(...),
    salary_expectation: int = Form(...)
):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    content = await file.read()
    
    # 1. Parse PDF
    parser = ResumeParser()
    try:
        extracted = parser.parse(content)
    except Exception as e:
        print(f"Resume parsing error: {e}")
        raise HTTPException(status_code=400, detail="Error parsing PDF: " + str(e))
    if not extracted:
        print("Resume parser returned empty result")
        raise HTTPException(status_code=400, detail="PDF is empty or could not be parsed")
    
    extracted['location'] = location
    extracted['salary_expectation'] = salary_expectation

    # 2. Generate Embedding
    embedding_service = EmbeddingService()
    embedding = embedding_service.get_embedding(extracted['extracted_text'])
    if not embedding:
        print("Warning: embedding service returned empty, using zero-vector fallback")
        embedding = [0.0] * 768
    extracted['embedding'] = embedding

    # 3. Fraud Detection
    detector = FraudDetector()
    fraud_report = detector.analyze(extracted, [])
    
    # 4. Build resume data
    resume_data = {
        "email": extracted['email'],
        "extracted_text": extracted['extracted_text'],
        "skills": extracted['skills'],
        "experience_years": extracted['experience_years'],
        "location": extracted['location'],
        "salary_expectation": extracted['salary_expectation'],
        "embedding": extracted['embedding'],
        "trust_score": fraud_report['trust_score'],
        "fraud_flags": fraud_report['fraud_flags'],
        "risk_level": fraud_report['risk_level']
    }
    
    # Try to store in databases
    supabase = get_supabase()
    saved_resume = resume_data.copy()
    saved_resume['id'] = "local-" + str(int(datetime.utcnow().timestamp()))

    # always keep local copy (could use sqlite_db.insert_job_local analog but for resumes)
    # for simplicity we'll skip persistence now, only analyze

    if supabase is not None:
        try:
            insert_resp = supabase.table("resumes").insert(resume_data).execute()
            if insert_resp.data:
                saved_resume = insert_resp.data[0]
                print(f"Resume saved with ID: {saved_resume.get('id')}")
        except Exception as e:
            print(f"Database error on insert: {e}")
            # ignore
            pass
    else:
        print("Database unavailable; running in demo mode")

    # 5. match against available jobs
    jobs = []
    # try supabase first
    if supabase is not None:
        try:
            jobs_resp = supabase.table("jobs").select("*").execute()
            jobs = jobs_resp.data or []
        except Exception as e:
            print("Error fetching jobs from Supabase, falling back to local", e)
    if not jobs:
        # get local jobs from sqlite
        from backend.services.sqlite_db import get_all_jobs_local
        jobs = get_all_jobs_local()

    matcher = MatchingEngine()
    match_results = []
    for job in jobs:
        score = matcher.calculate_score(resume_data, job)
        match_results.append({"job": job, "score": score})

    # sort by final_score desc
    match_results.sort(key=lambda x: x['score']['final_match_score'], reverse=True)

    # Return results including top matches
    return {
        "success": True,
        "resume": saved_resume,
        "fraud_report": fraud_report,
        "matches": match_results
    }
