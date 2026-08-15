-- =============================================================================
-- AVENZO — PostgreSQL Initialization Script
-- This runs automatically when the Docker container starts fresh.
-- Creates database extensions needed by the application.
-- =============================================================================

-- Enable UUID generation (used for all primary keys)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Enable full-text search
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Log initialization
DO $$
BEGIN
    RAISE NOTICE 'AVENZO database extensions initialized successfully';
    RAISE NOTICE 'UUID, pgcrypto, pg_trgm extensions loaded';
    RAISE NOTICE 'Run Alembic migrations next: alembic upgrade head';
END $$;
