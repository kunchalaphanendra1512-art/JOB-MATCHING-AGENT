import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

class AnalysisService:
    def __init__(self):
        if not GEMINI_API_KEY:
            self.model = None
        else:
            genai.configure(api_key=GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-1.5-flash')

    def analyze_resume_match(self, resume_text: str, job_description: str) -> dict:
        """
        Performs deep analysis of a resume against a job description using Gemini 1.5 Flash.
        Returns structured JSON with scores, skills, and suggestions.
        """
        if not self.model:
            return {
                "match_score": 0,
                "matching_skills": [],
                "missing_skills": [],
                "improvement_suggestions": ["AI analysis unavailable. Please check API key."],
                "risk_analysis": "Medium"
            }

        prompt = f"""
        You are a senior technical recruiter. Analyze the following resume against the job description.
        
        Resume:
        {resume_text}
        
        Job Description:
        {job_description}
        
        Return a JSON object with the following structure:
        {{
            "match_score": (integer 0-100),
            "matching_skills": (list of strings),
            "missing_skills": (list of strings),
            "improvement_suggestions": (list of strings),
            "risk_analysis": ("Low" | "Medium" | "High")
        }}
        
        Return ONLY the JSON.
        """
        
        try:
            response = self.model.generate_content(prompt)
            # Clean response text in case of markdown blocks
            text = response.text.strip()
            if text.startswith("```json"):
                text = text.replace("```json", "").replace("```", "").strip()
            
            return json.loads(text)
        except Exception as e:
            print(f"Gemini Analysis Error: {e}")
            return {
                "match_score": 0,
                "matching_skills": [],
                "missing_skills": [],
                "improvement_suggestions": [f"Error during analysis: {str(e)}"],
                "risk_analysis": "High"
            }
