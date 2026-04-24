-- Week 1 schema: documents + chunks
-- Run with:
--   psql -U postgres -d rag_lab -f sql/schema.sql

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

DROP TABLE IF EXISTS chunks;
DROP TABLE IF EXISTS documents;

CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    source TEXT,
    created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL
        REFERENCES documents(id)
        ON DELETE CASCADE,
    content TEXT NOT NULL,
    chunk_index INT NOT NULL,
    created_at TIMESTAMP DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON chunks(document_id);
