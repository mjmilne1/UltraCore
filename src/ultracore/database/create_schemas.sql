-- UltraCore PostgreSQL Schemas
-- Data Mesh: Separate schemas per domain

-- Create schemas for each domain
CREATE SCHEMA IF NOT EXISTS customers;
CREATE SCHEMA IF NOT EXISTS accounts;
CREATE SCHEMA IF NOT EXISTS lending;

-- Comments
COMMENT ON SCHEMA customers IS 'Customer domain data';
COMMENT ON SCHEMA accounts IS 'Account and transaction data';
COMMENT ON SCHEMA lending IS 'Loan and lending data';

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pg_trgm for text search
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Enable btree_gin for multi-column indexes
CREATE EXTENSION IF NOT EXISTS btree_gin;
