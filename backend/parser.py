import pdfplumber
import io
import re

class ResumeParser:
    def parse(self, pdf_bytes):
        text = ""
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                text += page.extract_text() + "\n"
        
        return {
            "full_text": text,
            "email": self.extract_email(text),
            "skills": self.extract_skills(text),
            "experience_years": self.estimate_experience(text)
        }

    def extract_email(self, text):
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        match = re.search(email_pattern, text)
        return match.group(0) if match else None

    def extract_skills(self, text):
        # Simplified skill extraction for demo
        common_skills = ["Python", "React", "TypeScript", "SQL", "Machine Learning", "AWS", "Docker"]
        found = [skill for skill in common_skills if skill.lower() in text.lower()]
        return found

    def estimate_experience(self, text):
        # Simplified logic: look for "years" near numbers
        matches = re.findall(r'(\d+)\+?\s*years?', text.lower())
        if matches:
            return max([int(m) for m in matches])
        return 0
