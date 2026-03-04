-- HireSense AI Advanced Database Schema

-- Enable Vector Extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Users Table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    role TEXT CHECK (role IN ('candidate', 'recruiter')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Resumes Table
CREATE TABLE IF NOT EXISTS resumes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    email TEXT,
    extracted_text TEXT,
    skills JSONB DEFAULT '[]',
    experience_years INTEGER,
    location TEXT,
    salary_expectation INTEGER,
    summary TEXT,
    embedding VECTOR(1536),
    trust_score INTEGER DEFAULT 100,
    fraud_flags JSONB DEFAULT '[]',
    risk_level TEXT CHECK (risk_level IN ('Low', 'Medium', 'High')),
    interview_questions TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Jobs Table
CREATE TABLE IF NOT EXISTS jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recruiter_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title TEXT,
    description TEXT,
    required_skills JSONB DEFAULT '[]',
    required_experience INTEGER,
    location TEXT,
    salary_range_min INTEGER,
    salary_range_max INTEGER,
    embedding VECTOR(1536),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Matches Table
CREATE TABLE IF NOT EXISTS matches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resume_id UUID REFERENCES resumes(id) ON DELETE CASCADE,
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
    skill_score FLOAT,
    experience_score FLOAT,
    location_score FLOAT,
    salary_score FLOAT,
    semantic_score FLOAT,
    final_match_score FLOAT,
    explanation TEXT,
    rank INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
