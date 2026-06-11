'use strict';

/**
 * seed_roles.js — one-shot seeder for RadOps role-based test data.
 *
 * Creates:
 *   3 × radiologist  (Dr. Sarah Mitchell, Dr. James Patterson, Dr. Priya Sharma)
 *   3 × technician   (Alex Nguyen, Marcus Williams, Sofia Chen)
 *   2 × manager      (Dr. Rachel Torres, Dr. Kevin O'Brien)
 *   1 × admin        (System Administrator)
 *
 * Each user gets realistic sessions + events that reflect their role's
 * typical navigation pattern, so the Role Analysis charts show clear
 * differences between groups.
 *
 * Default password for all seeded accounts: RadOps2024!
 *
 * Usage:
 *   node seed_roles.js           — safe; exits if data already exists
 *   node seed_roles.js --force   — re-seeds even if data exists (adds more sessions)
 */

require('dotenv').config();
const { Pool } = require('pg');
const bcrypt   = require('bcrypt');
const crypto   = require('crypto');

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: { rejectUnauthorized: false },
});

// ── User definitions ──────────────────────────────────────────────────────

const SEED_USERS = [
  // radiologist — heavy Radiology + Reports, deep back-and-forth paths
  { name: 'Dr. Sarah Mitchell',   email: 'sarah.mitchell@radops.internal',  role: 'radiologist' },
  { name: 'Dr. James Patterson',  email: 'james.patterson@radops.internal', role: 'radiologist' },
  { name: 'Dr. Priya Sharma',     email: 'priya.sharma@radops.internal',    role: 'radiologist' },

  // technician — System-heavy, some Radiology quality checks
  { name: 'Alex Nguyen',          email: 'alex.nguyen@radops.internal',     role: 'technician' },
  { name: 'Marcus Williams',      email: 'marcus.williams@radops.internal', role: 'technician' },
  { name: 'Sofia Chen',           email: 'sofia.chen@radops.internal',      role: 'technician' },

  // manager — Overview + Reports oversight, fewer deeper sessions
  { name: 'Dr. Rachel Torres',    email: 'rachel.torres@radops.internal',   role: 'manager' },
  { name: "Dr. Kevin O'Brien",    email: 'kevin.obrien@radops.internal',    role: 'manager' },

  // admin — all sections, system maintenance focus
  { name: 'System Administrator', email: 'admin@radops.internal',           role: 'admin' },
];

// ── Session templates ─────────────────────────────────────────────────────
// path    : sections visited in order (revisits allowed)
// timings : ms spent at each step  (same length as path)
// daysAgo : how many days before today the session started
// hour    : hour-of-day (24h) — reflects work schedule per role

const RADIOLOGIST_SESSIONS = [
  // Deep diagnostic session — reads scans, writes report, revisits
  { path: ['overview', 'radiology', 'reports', 'radiology', 'reports'],
    timings: [45000, 480000, 195000, 420000, 210000], daysAgo: 1,  hour: 9  },
  // Back-to-back radiology reads before reporting
  { path: ['overview', 'radiology', 'radiology', 'reports'],
    timings: [35000, 540000, 360000, 255000],          daysAgo: 2,  hour: 10 },
  // Quick consult then report
  { path: ['overview', 'radiology', 'reports', 'radiology'],
    timings: [50000, 390000, 165000, 300000],          daysAgo: 4,  hour: 14 },
  // Lighter day — fewer studies
  { path: ['overview', 'radiology', 'reports'],
    timings: [40000, 330000, 185000],                  daysAgo: 6,  hour: 11 },
  // Morning review loop
  { path: ['overview', 'radiology', 'reports', 'overview', 'reports'],
    timings: [60000, 510000, 200000, 30000, 180000],   daysAgo: 8,  hour: 8  },
];

const TECHNICIAN_SESSIONS = [
  // Equipment setup + scan quality check
  { path: ['overview', 'system', 'radiology', 'system'],
    timings: [25000, 195000, 75000, 220000],            daysAgo: 1,  hour: 7  },
  // Troubleshooting — stays in System
  { path: ['overview', 'system', 'system'],
    timings: [20000, 255000, 180000],                   daysAgo: 2,  hour: 8  },
  // Scan handoff check
  { path: ['overview', 'radiology', 'system'],
    timings: [28000, 90000, 210000],                    daysAgo: 3,  hour: 13 },
  // Full equipment maintenance cycle
  { path: ['overview', 'system', 'radiology', 'system', 'system'],
    timings: [18000, 165000, 55000, 195000, 130000],    daysAgo: 5,  hour: 9  },
  // End-of-day system check
  { path: ['overview', 'system'],
    timings: [22000, 280000],                           daysAgo: 7,  hour: 16 },
];

const MANAGER_SESSIONS = [
  // Weekly KPI review — deep in Reports
  { path: ['overview', 'reports', 'overview'],
    timings: [125000, 510000, 85000],                   daysAgo: 1,  hour: 10 },
  // Monthly reporting session
  { path: ['overview', 'reports'],
    timings: [145000, 620000],                          daysAgo: 3,  hour: 14 },
  // Cross-section audit: radiology performance then report
  { path: ['overview', 'radiology', 'reports'],
    timings: [105000, 65000, 570000],                   daysAgo: 5,  hour: 9  },
  // End-of-week review with return to overview
  { path: ['overview', 'reports', 'overview', 'reports'],
    timings: [90000, 435000, 60000, 380000],            daysAgo: 9,  hour: 11 },
];

const ADMIN_SESSIONS = [
  // Full system tour + reporting check
  { path: ['overview', 'system', 'radiology', 'reports', 'system'],
    timings: [55000, 315000, 85000, 125000, 255000],    daysAgo: 1,  hour: 10 },
  // Maintenance window — long System stay
  { path: ['overview', 'system', 'system'],
    timings: [40000, 450000, 330000],                   daysAgo: 2,  hour: 7  },
  // Integration check across all sections
  { path: ['overview', 'radiology', 'system', 'reports'],
    timings: [50000, 70000, 390000, 110000],            daysAgo: 3,  hour: 15 },
  // Node maintenance with overview context
  { path: ['overview', 'system', 'overview', 'system'],
    timings: [35000, 510000, 30000, 420000],            daysAgo: 5,  hour: 9  },
  // After-hours emergency check
  { path: ['system', 'radiology', 'overview', 'reports'],
    timings: [260000, 55000, 75000, 145000],            daysAgo: 7,  hour: 21 },
  // Routine weekly audit
  { path: ['overview', 'system', 'reports', 'system'],
    timings: [45000, 375000, 95000, 300000],            daysAgo: 10, hour: 11 },
];

const ROLE_SESSIONS = {
  radiologist: RADIOLOGIST_SESSIONS,
  technician:  TECHNICIAN_SESSIONS,
  manager:     MANAGER_SESSIONS,
  admin:       ADMIN_SESSIONS,
};

// ── Helpers ───────────────────────────────────────────────────────────────

/** Apply consecutive dedup — same logic as db.js upsertAnalyticsSession. */
function consecutiveDedup(arr) {
  return arr.filter((v, i) => i === 0 || v !== arr[i - 1]);
}

/** Add ±pct random jitter so timings don't look machine-generated. */
function jitter(ms, pct = 0.15) {
  return Math.round(ms * (1 + (Math.random() * 2 - 1) * pct));
}

async function upsertUser(userDef, passwordHash) {
  const { rows } = await pool.query(
    `INSERT INTO users (oauth_provider, oauth_id, email, name, password_hash, role, last_login)
     VALUES ('local', $1, $1, $2, $3, $4, NOW())
     ON CONFLICT (oauth_id) DO UPDATE
       SET name       = EXCLUDED.name,
           role       = EXCLUDED.role,
           last_login = NOW()
     RETURNING id, name, role`,
    [userDef.email, userDef.name, passwordHash, userDef.role],
  );
  return rows[0];
}

async function seedSession(userId, template, dayShift = 0) {
  const { path, timings, daysAgo, hour } = template;

  const sessionId = crypto.randomUUID();

  const startedAt = new Date();
  startedAt.setDate(startedAt.getDate() - (daysAgo + dayShift));
  startedAt.setHours(hour, Math.floor(Math.random() * 50), 0, 0);

  const jTimings   = timings.map(t => jitter(t));
  const totalMs    = jTimings.reduce((a, b) => a + b, 0);
  const lastSeenAt = new Date(startedAt.getTime() + totalMs);

  await pool.query(
    `INSERT INTO analytics_sessions
       (session_id, user_id, auth_method, section_flow, started_at, last_seen_at)
     VALUES ($1, $2, 'credentials', $3, $4, $5)
     ON CONFLICT (session_id) DO NOTHING`,
    [sessionId, userId, consecutiveDedup(path), startedAt, lastSeenAt],
  );

  let ts = new Date(startedAt);
  for (let i = 0; i < path.length; i++) {
    const section     = path[i];
    const spentMs     = jTimings[i];
    const flowPos     = i + 1;

    await pool.query(
      `INSERT INTO analytics_events
         (session_id, user_id, auth_method, section, event, time_spent_ms, flow_position, ts)
       VALUES ($1,$2,'credentials',$3,'section_enter',NULL,$4,$5)`,
      [sessionId, userId, section, flowPos, ts],
    );

    const exitTs = new Date(ts.getTime() + spentMs);
    await pool.query(
      `INSERT INTO analytics_events
         (session_id, user_id, auth_method, section, event, time_spent_ms, flow_position, ts)
       VALUES ($1,$2,'credentials',$3,'section_exit',$4,$5,$6)`,
      [sessionId, userId, section, spentMs, flowPos, exitTs],
    );

    ts = exitTs;
  }

  return { sessionId, depth: path.length, totalMin: (totalMs / 60000).toFixed(1) };
}

// ── Guard ─────────────────────────────────────────────────────────────────

async function alreadySeeded() {
  const emails = SEED_USERS.map(u => u.email);
  const { rows } = await pool.query(
    `SELECT COUNT(*)::int AS n
     FROM users u
     JOIN analytics_sessions s ON s.user_id = u.id
     WHERE u.email = ANY($1)`,
    [emails],
  );
  return rows[0].n > 0;
}

// ── Main ──────────────────────────────────────────────────────────────────

async function main() {
  const force = process.argv.includes('--force');

  if (!force && await alreadySeeded()) {
    console.log('⚠  Seed data already exists — skipping.');
    console.log('   Run with --force to re-seed (will add additional sessions).');
    return;
  }

  console.log('RadOps role seed — default password: RadOps2024!\n');
  const passwordHash = await bcrypt.hash('RadOps2024!', 12);

  // Stagger each user's sessions by 0–2 days so timestamps look natural
  for (let ui = 0; ui < SEED_USERS.length; ui++) {
    const userDef  = SEED_USERS[ui];
    const user     = await upsertUser(userDef, passwordHash);
    const dayShift = ui % 3;   // 0, 1, or 2 day offset

    const templates = ROLE_SESSIONS[userDef.role] || [];
    let totalSessions = 0;

    for (const tpl of templates) {
      const result = await seedSession(user.id, tpl, dayShift);
      totalSessions++;
      console.log(
        `  [${user.role.padEnd(12)}] ${user.name.padEnd(28)} ` +
        `session ${result.sessionId.slice(0, 8)}…  ` +
        `depth=${String(result.depth).padStart(2)}  ${result.totalMin} min`,
      );
    }

    console.log(`  └─ ${totalSessions} sessions inserted for ${user.name}\n`);
  }

  console.log('Seed complete.\n');
  console.log('Role summary inserted:');
  console.log('  radiologist × 3  (5 sessions each)');
  console.log('  technician  × 3  (5 sessions each)');
  console.log('  manager     × 2  (4 sessions each)');
  console.log('  admin       × 1  (6 sessions)');
}

main()
  .catch(err => {
    console.error('\nSeed failed:', err.message);
    process.exit(1);
  })
  .finally(() => pool.end());
