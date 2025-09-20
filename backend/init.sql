-- CustomerCareGPT Database Initialization
-- This file is used by Docker Compose to initialize the database

-- Create the database if it doesn't exist
-- (This is handled by POSTGRES_DB environment variable)

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- The actual table creation is handled by SQLAlchemy/Alembic
-- This file is here to satisfy Docker Compose requirements
