import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

class InterviewGenerator:
    def __init__(self):
        if not GEMINI_API_KEY:
            self.model = None
        else:
            genai.configure(api_key=GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-1.5-flash')

    def generate(self, resume_skills: list, job_description: str, required_skills: list) -> list:
        """
        Generates 3 technical interview questions based on skill gaps using Gemini 1.5 Flash.
        """
        if not self.model:
            return [
                "Can you explain your experience with the core technologies mentioned in the job description?",
                "How would you handle a complex technical challenge in a fast-paced environment?",
                "Tell us about a project where you had to learn a new skill quickly to succeed."
            ]

        missing_skills = [s for s in required_skills if s not in resume_skills]
        
        prompt = f"""
        Candidate Skills: {', '.join(resume_skills)}
        Job Required Skills: {', '.join(required_skills)}
        Job Description: {job_description}
        
        Identify the skill gaps and generate 3 highly technical and specific interview questions.
        Return exactly 3 questions as a bulleted list.
        """
        
        try:
            response = self.model.generate_content(prompt)
            content = response.text
            questions = [q.strip("- ").strip("123. ") for q in content.split("\n") if q.strip()]
            return questions[:3]
        except Exception as e:
            print(f"Gemini Interview Generation Error: {e}")
            return ["Error generating questions. Please try again later."]
