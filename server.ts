import "dotenv/config";
import express from "express";
import { createServer as createViteServer } from "vite";
import path from "path";
import { createClient } from "@supabase/supabase-js";

// Supabase Initialization
const rawUrl = process.env.SUPABASE_URL?.trim();
const supabaseUrl = (rawUrl && rawUrl !== "YOUR_SUPABASE_URL" && rawUrl.startsWith('http')) 
  ? rawUrl 
  : "https://lwpiaxjcibjtmugzmiuy.supabase.co";

const rawKey = process.env.SUPABASE_ANON_KEY?.trim();
const supabaseKey = (rawKey && rawKey !== "YOUR_SUPABASE_ANON_KEY") 
  ? rawKey 
  : "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imx3cGlheGpjaWJqdG11Z3ptaXV5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzIxNzYyOTIsImV4cCI6MjA4Nzc1MjI5Mn0.EnqAEklzF7JFHq7Uhf80RKUO5PT09STrmvvTCakK6rU";

const supabase = createClient(supabaseUrl, supabaseKey);

// --- ML Logic Helpers ---

const cosineSimilarity = (vecA: number[], vecB: number[]) => {
  let dotProduct = 0;
  let normA = 0;
  let normB = 0;
  for (let i = 0; i < vecA.length; i++) {
    dotProduct += vecA[i] * vecB[i];
    normA += vecA[i] * vecA[i];
    normB += vecB[i] * vecB[i];
  }
  return dotProduct / (Math.sqrt(normA) * Math.sqrt(normB));
};

const calculateMatch = (resume: any, job: any) => {
  // 1. Skill Match (40%)
  const resumeSkills = new Set(resume.skills.map((s: string) => s.toLowerCase()));
  const jobSkills = job.required_skills.map((s: string) => s.toLowerCase());
  const skillOverlap = jobSkills.filter((s: string) => resumeSkills.has(s)).length;
  const skillScore = jobSkills.length > 0 ? (skillOverlap / jobSkills.length) * 100 : 100;

  // 2. Experience (20%)
  const expScore = resume.experience_years >= job.required_experience 
    ? 100 
    : (resume.experience_years / job.required_experience) * 100;

  // 3. Location (10%)
  const locScore = resume.location?.toLowerCase() === job.location?.toLowerCase() ? 100 : 30;

  // 4. Salary (10%)
  const salScore = (resume.salary_expectation >= job.salary_range_min && resume.salary_expectation <= job.salary_range_max) ? 100 : 0;

  // 5. Semantic Similarity (20%)
  const semScore = cosineSimilarity(resume.embedding, job.embedding) * 100;

  const finalScore = (skillScore * 0.4) + (expScore * 0.2) + (locScore * 0.1) + (salScore * 0.1) + (semScore * 0.2);

  return {
    skill_score: skillScore,
    experience_score: expScore,
    location_score: locScore,
    salary_score: salScore,
    semantic_score: semScore,
    final_match_score: finalScore
  };
};

const detectFraud = (resume: any, allResumes: any[]) => {
  let trustScore = 100;
  const flags = [];

  // 1. Duplicate detection (> 0.90)
  for (const other of allResumes) {
    if (other.id === resume.id) continue;
    if (cosineSimilarity(resume.embedding, other.embedding) > 0.90) {
      trustScore -= 20;
      flags.push("Duplicate profile detected");
      break;
    }
  }

  // 2. Skill stuffing (> 30 skills)
  if (resume.skills.length > 30) {
    trustScore -= 10;
    flags.push("Skill stuffing detected (>30 skills)");
  }

  // 3. Invalid email
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(resume.email)) {
    trustScore -= 5;
    flags.push("Invalid email format");
  }

  // 4. Unrealistic experience
  if (resume.experience_years > 50) {
    trustScore -= 10;
    flags.push("Unrealistic experience timeline");
  }

  const riskLevel = trustScore < 60 ? "High" : trustScore < 80 ? "Medium" : "Low";

  return { trustScore, flags, riskLevel };
};

// --- Server Setup ---

async function startServer() {
  const app = express();
  const PORT = 3000;

  app.use(express.json({ limit: '50mb' }));

  // --- API Routes ---

  app.post("/api/jobs", async (req, res) => {
    const { data, error } = await supabase.from('jobs').insert([req.body]).select();
    if (error) return res.status(500).json({ error: error.message });
    res.json(data[0]);
  });

  app.get("/api/jobs", async (req, res) => {
    const { data, error } = await supabase.from('jobs').select('*').order('created_at', { ascending: false });
    if (error) return res.status(500).json({ error: error.message });
    res.json(data);
  });

  app.post("/api/resumes", async (req, res) => {
    try {
      const resume = req.body;
      const { data: allResumes } = await supabase.from('resumes').select('id, embedding');
      
      const fraud = detectFraud(resume, allResumes || []);
      resume.trust_score = fraud.trustScore;
      resume.fraud_flags = fraud.flags;
      resume.risk_level = fraud.riskLevel;

      const { data, error } = await supabase.from('resumes').insert([resume]).select();
      if (error) throw error;
      
      const savedResume = data[0];

      // Immediate matching against all jobs
      const { data: jobs } = await supabase.from('jobs').select('*');
      if (jobs) {
        const matchRecords = jobs.map(job => ({
          resume_id: savedResume.id,
          job_id: job.id,
          ...calculateMatch(savedResume, job)
        }));
        await supabase.from('matches').insert(matchRecords);
      }

      res.json(savedResume);
    } catch (err: any) {
      res.status(500).json({ error: err.message });
    }
  });

  app.get("/api/ranked/:jobId", async (req, res) => {
    const { data, error } = await supabase
      .from('matches')
      .select('*, resume:resumes(*)')
      .eq('job_id', req.params.jobId)
      .order('final_match_score', { ascending: false });
    
    if (error) return res.status(500).json({ error: error.message });
    res.json(data);
  });

  app.get("/api/analytics", async (req, res) => {
    const { data: resumes } = await supabase.from('resumes').select('trust_score, fraud_flags, skills');
    const { data: matches } = await supabase.from('matches').select('final_match_score');

    const total = resumes?.length || 0;
    const fraudCount = resumes?.filter(r => r.fraud_flags?.length > 0).length || 0;
    const avgMatch = matches?.length ? matches.reduce((acc, m) => acc + m.final_match_score, 0) / matches.length : 0;
    
    const skillCounts: any = {};
    resumes?.forEach(r => r.skills?.forEach((s: string) => skillCounts[s] = (skillCounts[s] || 0) + 1));
    const topSkills = Object.entries(skillCounts).sort((a: any, b: any) => b[1] - a[1]).slice(0, 5).map(e => e[0]);

    res.json({
      avg_match_score: avgMatch,
      fraud_percentage: total > 0 ? (fraudCount / total) * 100 : 0,
      top_demanded_skills: topSkills,
      total_candidates: total,
      confidence_metric: 96.5 // Simulated confidence
    });
  });

  // Vite Middleware
  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({ server: { middlewareMode: true }, appType: "spa" });
    app.use(vite.middlewares);
  } else {
    app.use(express.static("dist"));
    app.get("*", (req, res) => res.sendFile(path.resolve("dist/index.html")));
  }

  app.listen(PORT, "0.0.0.0", () => console.log(`Server running on port ${PORT}`));
}

startServer();
