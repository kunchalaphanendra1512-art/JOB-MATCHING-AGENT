// HireSense AI - Matching & Fraud Detection Logic (TypeScript)

export interface ResumeData {
  id: string;
  skills: string[];
  experience_years: number;
  location: string;
  salary_expectation: number;
  embedding: number[];
  extracted_text: string;
}

export interface JobData {
  id: string;
  required_skills: string[];
  required_experience: number;
  location: string;
  salary_range: { min: number; max: number };
  embedding: number[];
}

export class MatchingEngine {
  static calculateSkillScore(resumeSkills: string[], jobSkills: string[]): number {
    if (jobSkills.length === 0) return 100;
    const resumeSet = new Set(resumeSkills.map(s => s.toLowerCase()));
    const intersection = jobSkills.filter(s => resumeSet.has(s.toLowerCase()));
    return (intersection.length / jobSkills.length) * 100;
  }

  static calculateExperienceScore(candidateExp: number, requiredExp: number): number {
    if (candidateExp >= requiredExp) return 100;
    return requiredExp > 0 ? (candidateExp / requiredExp) * 100 : 100;
  }

  static calculateLocationScore(candidateLoc: string, jobLoc: string): number {
    if (candidateLoc.toLowerCase() === jobLoc.toLowerCase()) return 100;
    // Simple state check
    const candParts = candidateLoc.split(',').map(p => p.trim());
    const jobParts = jobLoc.split(',').map(p => p.trim());
    if (candParts.length > 1 && jobParts.length > 1) {
      if (candParts[candParts.length - 1] === jobParts[jobParts.length - 1]) return 70;
    }
    return 30;
  }

  static calculateSalaryScore(expectation: number, range: { min: number; max: number }): number {
    if (expectation >= range.min && expectation <= range.max) return 100;
    return 0;
  }

  static cosineSimilarity(vecA: number[], vecB: number[]): number {
    let dotProduct = 0;
    let normA = 0;
    let normB = 0;
    for (let i = 0; i < vecA.length; i++) {
      dotProduct += vecA[i] * vecB[i];
      normA += vecA[i] * vecA[i];
      normB += vecB[i] * vecB[i];
    }
    return dotProduct / (Math.sqrt(normA) * Math.sqrt(normB));
  }

  static match(resume: ResumeData, job: JobData) {
    const skillScore = this.calculateSkillScore(resume.skills, job.required_skills);
    const expScore = this.calculateExperienceScore(resume.experience_years, job.required_experience);
    const locScore = this.calculateLocationScore(resume.location, job.location);
    const salScore = this.calculateSalaryScore(resume.salary_expectation, job.salary_range);
    const semScore = this.cosineSimilarity(resume.embedding, job.embedding) * 100;

    const finalScore = (
      (skillScore * 0.4) +
      (expScore * 0.2) +
      (locScore * 0.1) +
      (salScore * 0.1) +
      (semScore * 0.2)
    );

    return {
      skill_score: skillScore,
      experience_score: expScore,
      location_score: locScore,
      salary_score: salScore,
      semantic_score: semScore,
      final_match_score: finalScore,
      explanation: `Matched ${Math.round(skillScore)}% of skills. Experience is ${expScore === 100 ? 'sufficient' : 'below requirement'}.`
    };
  }
}

export class FraudDetector {
  static detect(resume: ResumeData, allResumes: ResumeData[]) {
    let trustScore = 100;
    const flags: string[] = [];

    // 1. Duplicate detection
    for (const other of allResumes) {
      if (other.id === resume.id) continue;
      const sim = MatchingEngine.cosineSimilarity(resume.embedding, other.embedding);
      if (sim > 0.90) {
        trustScore -= 20;
        flags.push("Duplicate profile detected (High similarity with existing profile)");
        break;
      }
    }

    // 2. Skill stuffing
    if (resume.skills.length > 30) {
      trustScore -= 10;
      flags.push("Skill stuffing detected (>30 skills)");
    }

    // 3. Contact validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(resume.extracted_text)) {
      // Very loose check since extracted_text might be messy
      if (!resume.extracted_text.includes('@')) {
        trustScore -= 5;
        flags.push("Invalid or missing contact format");
      }
    }

    // 4. Unrealistic experience
    if (resume.experience_years > 50) {
      trustScore -= 10;
      flags.push("Unrealistic experience timeline (>50 years)");
    }

    return {
      trust_score: Math.max(0, trustScore),
      fraud_flags: flags
    };
  }
}
