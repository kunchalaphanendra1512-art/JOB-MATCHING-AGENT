import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.routers import resume, jobs, analytics, matches, candidates, debug
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(
    title="HireSense AI – Intelligent Job Matching & Validation Engine",
    description="Python ML backend for intelligent talent validation.",
    version="2.1.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(resume.router, prefix="/api", tags=["Resume"])
app.include_router(jobs.router, prefix="/api", tags=["Jobs"])
app.include_router(candidates.router, prefix="/api", tags=["Candidates"])
app.include_router(analytics.router, prefix="/api", tags=["Analytics"])
app.include_router(matches.router, prefix="/api", tags=["Matches"])
app.include_router(debug.router, prefix="/api", tags=["Debug"])

# Serve Static Files (React Frontend)
if os.path.exists("dist"):
    # Mount assets specifically so they are served directly
    if os.path.exists("dist/assets"):
        app.mount("/assets", StaticFiles(directory="dist/assets"), name="assets")

@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    # 1. Skip API routes (they are handled by routers above)
    if full_path.startswith("api"):
        raise HTTPException(status_code=404, detail="API route not found")
    
    # 2. Check if the file exists in dist (for robots.txt, favicon.ico, etc)
    file_path = os.path.join("dist", full_path)
    if os.path.isfile(file_path):
        return FileResponse(file_path)
    
    # 3. Fallback to index.html for SPA routing
    index_path = os.path.join("dist", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    
    return {"message": "HireSense AI Python Engine is Live"}

@app.get("/")
async def root():
    return {
        "message": "HireSense AI Python Engine is Live",
        "status": "Healthy",
        "version": "2.1.0"
    }

if __name__ == "__main__":
    import uvicorn
    # Render uses the PORT environment variable
    port = int(os.getenv("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
