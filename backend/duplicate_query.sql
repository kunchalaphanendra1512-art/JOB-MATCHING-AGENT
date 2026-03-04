-- SQL Query for Duplicate Detection using Vector Similarity
-- This query finds resumes that are highly similar to a given embedding

-- Replace :input_embedding with the 1536-dim vector
-- Replace :threshold with 0.90

SELECT 
    id, 
    email, 
    1 - (embedding <=> :input_embedding) AS similarity
FROM resumes
WHERE 1 - (embedding <=> :input_embedding) > :threshold
ORDER BY similarity DESC;

-- Note: <=> is the cosine distance operator in pgvector. 
-- 1 - distance = similarity.
