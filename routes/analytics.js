'use strict';

const { Router } = require('express');
const db = require('../db');

const router = Router();

// POST /api/analytics/event
// Called by the client tracker on every section_enter / section_exit.
// No auth required — tracker fires on page unload too (sendBeacon).
router.post('/event', async (req, res) => {
  const { session_id, user_id, auth_method, section, event, time_spent_ms, flow_position } = req.body;

  if (!session_id || !section || !event) {
    return res.status(400).json({ error: 'Missing required fields: session_id, section, event' });
  }

  try {
    await db.insertAnalyticsEvent({ session_id, user_id, auth_method, section, event, time_spent_ms, flow_position });
    await db.upsertAnalyticsSession({ session_id, user_id, auth_method, section });
    res.json({ ok: true });
  } catch (err) {
    console.error('Analytics event error:', err.message);
    res.status(500).json({ error: 'Internal error' });
  }
});

// GET /api/analytics/flow — how many times each section was visited
router.get('/flow', async (req, res) => {
  try {
    const { rows } = await db.pool.query(
      `SELECT section, COUNT(*) AS enter_count
       FROM analytics_events
       WHERE event = 'section_enter'
       GROUP BY section
       ORDER BY enter_count DESC`
    );
    res.json(rows);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// GET /api/analytics/time — average time spent per section (ms)
router.get('/time', async (req, res) => {
  try {
    const { rows } = await db.pool.query(
      `SELECT section,
              ROUND(AVG(time_spent_ms)) AS avg_ms,
              COUNT(*)                  AS sample_count
       FROM analytics_events
       WHERE event = 'section_exit' AND time_spent_ms IS NOT NULL
       GROUP BY section
       ORDER BY avg_ms DESC`
    );
    res.json(rows);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// GET /api/analytics/auth — session count + avg time per auth method
router.get('/auth', async (req, res) => {
  try {
    const { rows } = await db.pool.query(
      `SELECT auth_method,
              COUNT(DISTINCT session_id) AS sessions,
              ROUND(AVG(time_spent_ms))  AS avg_time_ms
       FROM analytics_events
       WHERE auth_method IS NOT NULL
       GROUP BY auth_method`
    );
    res.json(rows);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// GET /api/analytics/sessions — 50 most recent sessions with section flow
router.get('/sessions', async (req, res) => {
  try {
    const { rows } = await db.pool.query(
      `SELECT session_id, user_id, auth_method,
              started_at, last_seen_at, section_flow,
              array_length(section_flow, 1) AS sections_visited
       FROM analytics_sessions
       ORDER BY last_seen_at DESC
       LIMIT 50`
    );
    res.json(rows);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;
