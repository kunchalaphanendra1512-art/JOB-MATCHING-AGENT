import pdfplumber
import io
import re

class ResumeParser:
    def __init__(self):
        # Expanded skill patterns for NLP-like extraction
        self.skill_patterns = [
            "Python", "Java", "JavaScript", "TypeScript", "React", "Node.js", 
            "Express", "FastAPI", "SQL", "PostgreSQL", "MySQL", "MongoDB", "SQLite", 
            "Docker", "Kubernetes", "AWS", "Azure", "GCP", "Machine Learning", "Deep Learning",
            "NLP", "PyTorch", "TensorFlow", "Scikit-learn", "Pandas", "NumPy",
            "HTML", "CSS", "Sass", "Less", "GraphQL", "REST", "Git", "GitHub", "Agile", "Scrum",
            "Jira", "C++", "Go", "Rust", "Swift", "Kotlin", "PHP", "Ruby", "C#", ".NET",
            "Tableau", "PowerBI", "Spark", "Hadoop", "Kafka", "Redis", "Bootstrap", "Tailwind"
        ]

    def extract_text(self, file_bytes: bytes) -> str:
        text = ""
        try:
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            print(f"PDF Extraction Error: {e}")
            return ""
        return text.strip()

    def extract_skills(self, text: str) -> list:
        found_skills = []
        for skill in self.skill_patterns:
            # Use regex for word boundary matching
            if re.search(rf"\b{re.escape(skill)}\b", text, re.IGNORECASE):
                found_skills.append(skill)
        return list(set(found_skills))

    def estimate_experience(self, text: str) -> int:
        # Look for patterns like "5 years", "3+ years"
        patterns = [
            r"(\d+)\+?\s*years?\s*(?:of)?\s*(?:experience|work|relevant)",
            r"(?:experience|work)\s*(?:of)?\s*(\d+)\+?\s*years?"
        ]
        years = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for m in matches:
                years.append(int(m))
        
        return max(years) if years else 0

    def extract_email(self, text: str) -> str:
        email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
        match = re.search(email_pattern, text)
        return match.group(0) if match else "unknown@example.com"

    def parse(self, file_bytes: bytes) -> dict:
        text = self.extract_text(file_bytes)
        if not text:
            return {}

        parsed = {
            "extracted_text": text,
            "skills": self.extract_skills(text),
            "experience_years": self.estimate_experience(text),
            "email": self.extract_email(text)
        }
        # simple education detection (bachelor/master/PhD)
        edu_pattern = r"(Bachelor|Master|B\.Sc|M\.Sc|PhD|Doctorate)"
        m = re.search(edu_pattern, text, re.IGNORECASE)
        parsed["education"] = m.group(0) if m else ""
        # count project words as naive proxy
        parsed["projects_count"] = len(re.findall(r"project", text, re.IGNORECASE))
        return parsed
