# RadOps Analytics — Metabase Setup Guide

## 1. Run the DB migration first

Open the **Neon SQL Editor** (console.neon.tech → your project → SQL Editor) and run the entire contents of `analytics.sql`. This creates two tables:

| Table | Purpose |
|---|---|
| `analytics_events` | One row per section enter/exit — raw event log |
| `analytics_sessions` | One row per browser session — aggregated journey |

---

## 2. Connect Metabase to Neon

1. Open Metabase → **Admin panel** → **Databases** → **Add database**
2. Choose **PostgreSQL**
3. Fill in the connection details from your `.env` file:

| Field | Value |
|---|---|
| Host | (from DATABASE_URL — the `ep-xxx.region.neon.tech` part) |
| Port | `5432` |
| Database name | (from DATABASE_URL — the `/dbname` part) |
| Username | (from DATABASE_URL) |
| Password | (from DATABASE_URL) |
| SSL | **Required** — enable "Use a secure connection (SSL)" |

4. Click **Save** — Metabase will sync the schema automatically.

> Tip: You can paste the full Neon connection string into Metabase's "Connection string" field instead of filling each box manually.

---

## 3. Table schemas

### `analytics_events`

| Column | Type | Notes |
|---|---|---|
| `id` | BIGSERIAL | Primary key |
| `session_id` | VARCHAR(36) | UUID from `localStorage` |
| `user_id` | INTEGER | FK → `users.id`, nullable |
| `auth_method` | VARCHAR(20) | `'google'` or `'credentials'` |
| `section` | VARCHAR(30) | `'overview'`, `'radiology'`, `'system'`, `'reports'` |
| `event` | VARCHAR(30) | `'section_enter'` or `'section_exit'` |
| `time_spent_ms` | INTEGER | NULL for enter events; milliseconds on exit |
| `flow_position` | SMALLINT | 1-based position in this session's journey |
| `ts` | TIMESTAMPTZ | When the event occurred |

### `analytics_sessions`

| Column | Type | Notes |
|---|---|---|
| `session_id` | VARCHAR(36) | Primary key (UUID) |
| `user_id` | INTEGER | FK → `users.id`, nullable |
| `auth_method` | VARCHAR(20) | `'google'` or `'credentials'` |
| `started_at` | TIMESTAMPTZ | First event timestamp |
| `last_seen_at` | TIMESTAMPTZ | Most recent event timestamp |
| `section_flow` | TEXT[] | Ordered visited sections, e.g. `{overview,radiology,reports}` |

---

## 4. Suggested Metabase questions

Once connected, go to **New → Question → Raw data** and pick `analytics_events` or `analytics_sessions` to start exploring. Below are ready-to-use SQL queries — paste them via **New → SQL query**.

### Which sections do users visit most?
```sql
SELECT section, COUNT(*) AS visits
FROM analytics_events
WHERE event = 'section_enter'
GROUP BY section
ORDER BY visits DESC;
```

### Average time spent per section (seconds)
```sql
SELECT section,
       ROUND(AVG(time_spent_ms) / 1000.0, 1) AS avg_seconds,
       COUNT(*) AS samples
FROM analytics_events
WHERE event = 'section_exit' AND time_spent_ms IS NOT NULL
GROUP BY section
ORDER BY avg_seconds DESC;
```

### Google OAuth vs email/password — engagement comparison
```sql
SELECT auth_method,
       COUNT(DISTINCT session_id)              AS total_sessions,
       ROUND(AVG(time_spent_ms) / 1000.0, 1)  AS avg_sec_per_section
FROM analytics_events
WHERE auth_method IS NOT NULL
GROUP BY auth_method;
```

### Most common user journeys (top 10 section flows)
```sql
SELECT array_to_string(section_flow, ' → ') AS journey,
       COUNT(*) AS frequency
FROM analytics_sessions
GROUP BY section_flow
ORDER BY frequency DESC
LIMIT 10;
```

### Daily active sessions (last 30 days)
```sql
SELECT DATE(started_at) AS day, COUNT(*) AS sessions
FROM analytics_sessions
WHERE started_at >= NOW() - INTERVAL '30 days'
GROUP BY day
ORDER BY day;
```

### Drop-off — users who only visited overview and left
```sql
SELECT COUNT(*) AS single_section_sessions
FROM analytics_sessions
WHERE array_length(section_flow, 1) = 1
  AND section_flow[1] = 'overview';
```

---

## 5. Suggested dashboard layout in Metabase

Create a new **Dashboard** and add these cards:

1. **Bar chart** — section visit counts (question 1 above)
2. **Bar chart** — avg time per section in seconds (question 2)
3. **Row chart** — Google vs credentials sessions (question 3)
4. **Table** — top 10 user journeys (question 4)
5. **Line chart** — daily active sessions over 30 days (question 5)
6. **Number card** — single-section drop-off count (question 6)

---

## 6. API endpoints (for manual testing)

These are available without login while the server is running:

| Method | URL | Returns |
|---|---|---|
| `GET` | `/api/analytics/flow` | Section visit counts |
| `GET` | `/api/analytics/time` | Avg time per section |
| `GET` | `/api/analytics/auth` | Sessions by auth method |
| `GET` | `/api/analytics/sessions` | Last 50 sessions with flow |

Test with: `curl http://localhost:3000/api/analytics/flow`
