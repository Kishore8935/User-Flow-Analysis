// db.js — Neon PostgreSQL connection pool
// Uses the DATABASE_URL from your .env file.
// Neon requires SSL; the `ssl: { rejectUnauthorized: false }` flag
// handles that automatically for hosted Neon connections.

'use strict';

require('dotenv').config();
const { Pool } = require('pg');

if (!process.env.DATABASE_URL) {
  throw new Error(
    '❌  DATABASE_URL is not set in your .env file.\n' +
    '    Copy your Neon connection string and add it:\n' +
    '    DATABASE_URL=postgres://user:pass@ep-xxx.neon.tech/dbname?sslmode=require'
  );
}

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: { rejectUnauthorized: false }, // required for Neon
  max: 10,                            // max connections in pool
  idleTimeoutMillis: 30_000,          // close idle connections after 30s
  connectionTimeoutMillis: 5_000,     // fail fast if can't connect
});

// Log when a new client connects (helpful for debugging)
pool.on('connect', () => {
  console.log('🗄️   New DB client connected from pool');
});

pool.on('error', (err) => {
  console.error('❌  Unexpected DB pool error:', err.message);
});

// ── Convenience helpers ───────────────────────────────────────

/**
 * Run a query. Use parameterised queries to prevent SQL injection:
 *   db.query('SELECT * FROM users WHERE id = $1', [userId])
 */
async function query(text, params) {
  const start = Date.now();
  const result = await pool.query(text, params);
  const duration = Date.now() - start;
  console.log(`📋  DB query (${duration}ms): ${text.slice(0, 80)}`);
  return result;
}

/**
 * Test the connection — call this on server startup.
 * Resolves with the DB version string, or rejects on failure.
 */
async function testConnection() {
  const { rows } = await pool.query('SELECT version()');
  return rows[0].version;
}

/**
 * Upsert a user after OAuth login:
 *  - If the user doesn't exist → INSERT
 *  - If they do → UPDATE last_login, name, avatar_url
 * Returns the full user row.
 */
async function upsertUser({ oauth_provider, oauth_id, email, name, avatar_url }) {
  const sql = `
    INSERT INTO users (oauth_provider, oauth_id, email, name, avatar_url, last_login)
    VALUES ($1, $2, $3, $4, $5, NOW())
    ON CONFLICT (oauth_id) DO UPDATE
      SET name        = EXCLUDED.name,
          avatar_url  = EXCLUDED.avatar_url,
          email       = EXCLUDED.email,
          last_login  = NOW()
    RETURNING *;
  `;
  const { rows } = await pool.query(sql, [oauth_provider, oauth_id, email, name, avatar_url]);
  return rows[0];
}

/**
 * Find a user by their internal DB id (used to deserialise sessions).
 */
async function findUserById(id) {
  const { rows } = await pool.query('SELECT * FROM users WHERE id = $1', [id]);
  return rows[0] || null;
}

/**
 * Find a user by email — used by the local Passport strategy and registration.
 */
async function findUserByEmail(email) {
  const { rows } = await pool.query('SELECT * FROM users WHERE email = $1', [email]);
  return rows[0] || null;
}

/**
 * Create a new local (email + password) user.
 * oauth_id is set to the email since there is no OAuth provider id.
 */
async function createLocalUser(email, passwordHash) {
  const { rows } = await pool.query(
    `INSERT INTO users (oauth_provider, oauth_id, email, password_hash, last_login)
     VALUES ('local', $1, $2, $3, NOW())
     RETURNING *`,
    [email, email, passwordHash]
  );
  return rows[0];
}

/**
 * Return all users — for an admin view (Phase 5 optional).
 */
async function getAllUsers() {
  const { rows } = await pool.query(
    'SELECT id, name, email, oauth_provider, last_login, created_at FROM users ORDER BY created_at DESC'
  );
  return rows;
}

// ── Analytics helpers ─────────────────────────────────────────

async function insertAnalyticsEvent({ session_id, user_id, auth_method, section, event, time_spent_ms, flow_position }) {
  await pool.query(
    `INSERT INTO analytics_events
       (session_id, user_id, auth_method, section, event, time_spent_ms, flow_position)
     VALUES ($1, $2, $3, $4, $5, $6, $7)`,
    [session_id, user_id || null, auth_method || null, section, event, time_spent_ms || null, flow_position || null]
  );
}

async function upsertAnalyticsSession({ session_id, user_id, auth_method, section }) {
  await pool.query(
    `INSERT INTO analytics_sessions (session_id, user_id, auth_method, section_flow)
     VALUES ($1, $2, $3, ARRAY[$4]::TEXT[])
     ON CONFLICT (session_id) DO UPDATE
       SET last_seen_at = NOW(),
           user_id      = COALESCE(EXCLUDED.user_id, analytics_sessions.user_id),
           auth_method  = COALESCE(EXCLUDED.auth_method, analytics_sessions.auth_method),
           section_flow = CASE
             WHEN analytics_sessions.section_flow[array_length(analytics_sessions.section_flow,1)] = $4
               THEN analytics_sessions.section_flow
             ELSE analytics_sessions.section_flow || ARRAY[$4]::TEXT[]
           END`,
    [session_id, user_id || null, auth_method || null, section]
  );
}

module.exports = {
  query, testConnection, upsertUser, findUserById, findUserByEmail,
  createLocalUser, getAllUsers, insertAnalyticsEvent, upsertAnalyticsSession, pool
};
