"""Database helper and schema for HireSense AI

This module provides SQL statements for creating the required tables and a
convenience initializer using the Supabase client. It is not automatically
called; you may run the SQL manually or via `init_db()`.
"""
from backend.services.db import get_supabase

CREATE_JOBS_TABLE = r"""
CREATE TABLE IF NOT EXISTS jobs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    title text NOT NULL,
    required_skills text[] NOT NULL,
    preferred_skills text[] DEFAULT '{}',
    min_experience int NOT NULL,
    location text NOT NULL,
    role_type text NOT NULL,
    created_at timestamp with time zone DEFAULT now()
);
"""

CREATE_CANDIDATES_TABLE = r"""
CREATE TABLE IF NOT EXISTS candidates (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    email text NOT NULL,
    skills text[] NOT NULL,
    experience_years int NOT NULL,
    location text NOT NULL,
    education text DEFAULT '',
    projects_count int DEFAULT 0,
    created_at timestamp with time zone DEFAULT now()
);
"""

CREATE_MATCHES_TABLE = r"""
CREATE TABLE IF NOT EXISTS matches (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id uuid REFERENCES candidates(id),
    job_id uuid REFERENCES jobs(id),
    skill_score float,
    experience_score float,
    location_score float,
    final_score float,
    trust_score float,
    risk_level text,
    explanation text,
    created_at timestamp with time zone DEFAULT now()
);
"""


def init_db():
    supabase = get_supabase()
    if supabase is None:
        raise RuntimeError("Supabase client not configured")
    # execute raw SQL via the "sql" RPC if available or using python-postgrest
    try:
        supabase.rpc('sql', {'query': CREATE_JOBS_TABLE}).execute()
        supabase.rpc('sql', {'query': CREATE_CANDIDATES_TABLE}).execute()
        supabase.rpc('sql', {'query': CREATE_MATCHES_TABLE}).execute()
    except Exception as ex:
        print("Failed to initialize database:", ex)

