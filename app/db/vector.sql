-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create ivfflat indexes for embedding fields (cosine similarity)
-- lists parameter set to 100 (reasonable for up to 1M rows; adjust as data grows)

CREATE INDEX IF NOT EXISTS idx_gmail_cache_embedding ON gmail_cache
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_gcal_cache_embedding ON gcal_cache
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_gdrive_cache_embedding ON gdrive_cache
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
