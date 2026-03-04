# HireSense AI – Backend Setup & Deployment

## 🚀 Setup Instructions

### 1. Environment Variables
Create a `.env` file in the `backend/` directory with the following (DO NOT commit this file):
```env
GEMINI_API_KEY=your_gemini_api_key_here
SUPABASE_URL=your_supabase_url_here
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here
```

### 2. Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### 3. Run Locally
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## ☁️ Render Deployment Instructions

### 1. Create a New Web Service
- Connect your GitHub repository.
- Root Directory: `backend` (if you only want to deploy the backend).

### 2. Configuration
- **Runtime**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### 3. Environment Variables
Add the following in the Render dashboard (Environment tab):
- `GEMINI_API_KEY`
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `PYTHON_VERSION`: `3.11.0`

---

## 🧠 ML Engine Logic

### Matching Algorithm
The final score is a weighted sum:
- **Skill Match (40%)**: Intersection of resume skills and job requirements.
- **Experience (20%)**: Proportional score based on required years.
- **Location (10%)**: Binary match (100 or 30).
- **Salary (10%)**: Binary match (100 if within range).
- **Semantic (20%)**: Cosine similarity between Gemini embeddings.

### Deep Analysis
- **Gemini 1.5 Flash**: Performs deep semantic analysis to identify skill gaps and generate improvement suggestions.

---

## 📮 Postman Test Examples

### 1. Upload Resume
- **Method**: `POST`
- **URL**: `{{BASE_URL}}/api/upload-resume`
- **Body**: `form-data`
  - `file`: (Select PDF file)
  - `location`: "San Francisco, CA"
  - `salary_expectation`: 120000

### 2. Post Job
- **Method**: `POST`
- **URL**: `{{BASE_URL}}/api/post-job`
- **Body**: `json`
```json
{
  "title": "Senior Python Engineer",
  "description": "We are looking for a Python expert with FastAPI experience...",
  "required_skills": ["Python", "FastAPI", "PostgreSQL"],
  "required_experience": 5,
  "location": "San Francisco, CA",
  "salary_min": 100000,
  "salary_max": 150000
}
```
