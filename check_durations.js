'use strict';
require('dotenv').config();
const { Pool } = require('pg');
const pool = new Pool({ connectionString: process.env.DATABASE_URL, ssl: { rejectUnauthorized: false } });

(async () => {
  // Wall-clock durations (what the KPI currently shows)
  const { rows: wallclock } = await pool.query(`
    SELECT
      ROUND(AVG(EXTRACT(EPOCH FROM (last_seen_at - started_at)) / 60.0), 1) AS avg_wallclock_min,
      ROUND(MAX(EXTRACT(EPOCH FROM (last_seen_at - started_at)) / 60.0), 1) AS max_wallclock_min,
      ROUND(MIN(EXTRACT(EPOCH FROM (last_seen_at - started_at)) / 60.0), 1) AS min_wallclock_min
    FROM analytics_sessions
  `);
  console.log('Wall-clock (last_seen_at - started_at):');
  console.table(wallclock);

  // Actual tracked engagement (sum of time_spent_ms per session)
  const { rows: engagement } = await pool.query(`
    SELECT
      ROUND(AVG(session_ms) / 60000.0, 1) AS avg_engagement_min,
      ROUND(MAX(session_ms) / 60000.0, 1) AS max_engagement_min,
      ROUND(MIN(session_ms) / 60000.0, 1) AS min_engagement_min
    FROM (
      SELECT SUM(time_spent_ms) AS session_ms
      FROM analytics_events
      WHERE event = 'section_exit' AND time_spent_ms IS NOT NULL
      GROUP BY session_id
    ) t
  `);
  console.log('\nActual engagement (SUM of time_spent_ms per session):');
  console.table(engagement);

  // Show the worst offenders — longest wall-clock sessions
  const { rows: outliers } = await pool.query(`
    SELECT
      session_id,
      ROUND(EXTRACT(EPOCH FROM (last_seen_at - started_at)) / 60.0, 1) AS wallclock_min,
      TO_CHAR(started_at AT TIME ZONE 'Asia/Kolkata', 'DD Mon HH24:MI') AS started,
      TO_CHAR(last_seen_at AT TIME ZONE 'Asia/Kolkata', 'DD Mon HH24:MI') AS last_seen
    FROM analytics_sessions
    ORDER BY wallclock_min DESC
    LIMIT 10
  `);
  console.log('\nTop 10 longest wall-clock sessions:');
  console.table(outliers);

  await pool.end();
})().catch(e => { console.error(e.message); pool.end(); });
