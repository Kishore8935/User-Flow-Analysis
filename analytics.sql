-- ============================================================
-- RadOps Analytics — DB Migration
-- Run this manually in the Neon SQL Editor
-- (same way you ran schema.sql)
-- ============================================================

-- Events table — one row per section_enter / section_exit
CREATE TABLE IF NOT EXISTS analytics_events (
  id             BIGSERIAL    PRIMARY KEY,
  session_id     VARCHAR(36)  NOT NULL,
  user_id        INTEGER      REFERENCES users(id) ON DELETE SET NULL,
  auth_method    VARCHAR(20),
  section        VARCHAR(30)  NOT NULL,
  event          VARCHAR(30)  NOT NULL,       -- 'section_enter' or 'section_exit'
  time_spent_ms  INTEGER,                     -- NULL for enter events; set on exit
  flow_position  SMALLINT,                    -- ordinal within this session (1, 2, 3 …)
  ts             TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ae_session   ON analytics_events (session_id);
CREATE INDEX IF NOT EXISTS idx_ae_user      ON analytics_events (user_id);
CREATE INDEX IF NOT EXISTS idx_ae_auth      ON analytics_events (auth_method);
CREATE INDEX IF NOT EXISTS idx_ae_section   ON analytics_events (section);
CREATE INDEX IF NOT EXISTS idx_ae_ts        ON analytics_events (ts);

-- Sessions table — one row per browser session, updated on every event
CREATE TABLE IF NOT EXISTS analytics_sessions (
  session_id    VARCHAR(36)  PRIMARY KEY,
  user_id       INTEGER      REFERENCES users(id) ON DELETE SET NULL,
  auth_method   VARCHAR(20),
  started_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
  last_seen_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
  section_flow  TEXT[]       NOT NULL DEFAULT '{}'  -- e.g. {overview,radiology,reports}
);

CREATE INDEX IF NOT EXISTS idx_as_user      ON analytics_sessions (user_id);
CREATE INDEX IF NOT EXISTS idx_as_auth      ON analytics_sessions (auth_method);
CREATE INDEX IF NOT EXISTS idx_as_started   ON analytics_sessions (started_at);
