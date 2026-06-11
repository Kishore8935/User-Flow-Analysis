-- ================================================================
--  RadOps — Users Table Schema
--  Run this once in the Neon SQL Editor (or via psql)
-- ================================================================

CREATE TABLE IF NOT EXISTS users (
  id              SERIAL        PRIMARY KEY,
  oauth_provider  VARCHAR(50)   NOT NULL DEFAULT 'google',
  oauth_id        VARCHAR(255)  NOT NULL UNIQUE,
  email           VARCHAR(255)  UNIQUE,
  name            VARCHAR(255),
  avatar_url      TEXT,
  last_login      TIMESTAMP,
  created_at      TIMESTAMP     DEFAULT CURRENT_TIMESTAMP
);

-- Index for fast lookup by oauth_id (used on every login)
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_oauth_id ON users (oauth_id);

-- Index for fast lookup by email
CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);

-- Phase B: local email+password auth
ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash TEXT DEFAULT NULL;
