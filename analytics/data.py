import os
import pandas as pd
import psycopg2
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
DATABASE_URL = os.getenv('DATABASE_URL')


def _query(sql, params=None):
    conn = psycopg2.connect(DATABASE_URL)
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            cols = [d[0] for d in cur.description]
            rows = cur.fetchall()
        return pd.DataFrame(rows, columns=cols)
    finally:
        conn.close()


def get_users():
    return _query("""
        SELECT DISTINCT u.id,
               COALESCE(u.name, u.email, 'User #' || u.id::text) AS label
        FROM users u
        JOIN analytics_sessions s ON s.user_id = u.id
        ORDER BY label
    """)


def get_sessions(user_id):
    return _query("""
        SELECT session_id,
               TO_CHAR(started_at AT TIME ZONE 'Asia/Kolkata', 'DD Mon, HH24:MI IST') AS started_fmt,
               ROUND(EXTRACT(EPOCH FROM (last_seen_at - started_at)) / 60.0, 1)       AS duration_min,
               section_flow,
               array_length(section_flow, 1) AS sections_visited
        FROM analytics_sessions
        WHERE user_id = %s
        ORDER BY started_at DESC
    """, (user_id,))


def get_session_events(session_id):
    return _query("""
        SELECT section, event, time_spent_ms, flow_position, auth_method,
               (ts AT TIME ZONE 'Asia/Kolkata') AS ts_ist
        FROM analytics_events
        WHERE session_id = %s
        ORDER BY ts, flow_position
    """, (session_id,))


def get_section_stats():
    return _query("""
        SELECT section,
               COUNT(*) FILTER (WHERE event = 'section_enter')   AS visit_count,
               ROUND(
                 AVG(time_spent_ms) FILTER (WHERE event = 'section_exit') / 1000.0,
               1) AS avg_sec
        FROM analytics_events
        GROUP BY section
        ORDER BY visit_count DESC
    """)


def get_daily_sessions():
    return _query("""
        SELECT DATE(started_at AT TIME ZONE 'Asia/Kolkata') AS day,
               COUNT(*) AS sessions
        FROM analytics_sessions
        GROUP BY day
        ORDER BY day
    """)


def get_transition_matrix():
    return _query("""
        WITH t AS (
            SELECT session_id,
                   section AS from_section,
                   LEAD(section) OVER (PARTITION BY session_id ORDER BY ts) AS to_section
            FROM analytics_events
            WHERE event = 'section_enter'
        )
        SELECT from_section, to_section, COUNT(*) AS count
        FROM t
        WHERE to_section IS NOT NULL
        GROUP BY from_section, to_section
    """)


def get_funnel_data():
    return _query("""
        SELECT array_length(section_flow, 1) AS depth,
               COUNT(*) AS sessions
        FROM analytics_sessions
        WHERE array_length(section_flow, 1) IS NOT NULL
        GROUP BY depth
        ORDER BY depth
    """)


def get_auth_comparison():
    return _query("""
        SELECT auth_method,
               COUNT(DISTINCT session_id) AS sessions,
               ROUND(
                 AVG(time_spent_ms) FILTER (WHERE event = 'section_exit') / 1000.0,
               1) AS avg_sec
        FROM analytics_events
        WHERE auth_method IS NOT NULL
        GROUP BY auth_method
    """)


def get_path_continuation(path):
    """
    Given an ordered list of sections already taken (e.g. ['overview', 'radiology']),
    returns the distribution of what users visited at the NEXT step.
    Builds sequences from analytics_events so revisits are captured correctly.
    Empty path → distribution of first sections across all sessions.
    """
    n        = len(path)
    next_idx = n + 1  # PostgreSQL arrays are 1-indexed

    if n == 0:
        return _query("""
            WITH seqs AS (
                SELECT session_id,
                       ARRAY_AGG(section ORDER BY flow_position, ts) AS seq
                FROM analytics_events
                WHERE event = 'section_enter'
                GROUP BY session_id
            )
            SELECT seq[1]                                                       AS next_section,
                   COUNT(*)                                                     AS sessions,
                   ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1)          AS pct
            FROM seqs
            WHERE seq[1] IS NOT NULL
            GROUP BY next_section
            ORDER BY sessions DESC
        """)

    conditions = ' AND '.join(f"seq[{i + 1}] = %s" for i in range(n))
    sql = f"""
        WITH seqs AS (
            SELECT session_id,
                   ARRAY_AGG(section ORDER BY flow_position, ts) AS seq
            FROM analytics_events
            WHERE event = 'section_enter'
            GROUP BY session_id
        )
        SELECT COALESCE(seq[{next_idx}], '(session ended)')                AS next_section,
               COUNT(*)                                                     AS sessions,
               ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1)          AS pct
        FROM seqs
        WHERE {conditions}
        GROUP BY next_section
        ORDER BY sessions DESC
    """
    return _query(sql, tuple(path))


def get_all_user_flows():
    """One row per session — full ordered sequence as a raw list (includes revisits).
    Rebuilt from analytics_events so variable-length paths are captured correctly."""
    return _query("""
        WITH seqs AS (
            SELECT e.session_id,
                   ARRAY_AGG(e.section ORDER BY e.flow_position, e.ts) AS seq,
                   COUNT(*)::int                                        AS depth
            FROM analytics_events e
            WHERE e.event = 'section_enter'
            GROUP BY e.session_id
        )
        SELECT
            seqs.session_id,
            seqs.seq,
            seqs.depth,
            COALESCE(u.name, u.email, 'User #' || u.id::text)                   AS user_label,
            s.auth_method,
            COALESCE(u.role::text, 'unknown')                                    AS role,
            TO_CHAR(s.started_at AT TIME ZONE 'Asia/Kolkata', 'DD Mon HH24:MI') AS started_fmt,
            s.started_at
        FROM seqs
        JOIN analytics_sessions s ON s.session_id = seqs.session_id
        LEFT JOIN users u ON u.id = s.user_id
        ORDER BY s.started_at DESC
    """)


def get_dropoff_stats():
    """For each session, find the last section the user was in when they left.
    Returns distribution of exit sections + avg session duration."""
    return _query("""
        WITH last_exits AS (
            SELECT DISTINCT ON (session_id)
                session_id, section
            FROM analytics_events
            WHERE event = 'section_exit'
            ORDER BY session_id, ts DESC
        )
        SELECT
            le.section                                                              AS exit_section,
            COUNT(*)                                                                AS sessions,
            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1)                     AS pct,
            ROUND(AVG(
                EXTRACT(EPOCH FROM (s.last_seen_at - s.started_at)) / 60.0
            ), 1)                                                                   AS avg_min
        FROM last_exits le
        JOIN analytics_sessions s ON s.session_id = le.session_id
        GROUP BY le.section
        ORDER BY sessions DESC
    """)


def get_role_stats():
    """Per-role summary: session count, unique users, avg session duration, avg path depth."""
    return _query("""
        SELECT
            u.role::text                                                               AS role,
            COUNT(DISTINCT s.session_id)                                               AS sessions,
            COUNT(DISTINCT s.user_id)                                                  AS users,
            ROUND(AVG(
                EXTRACT(EPOCH FROM (s.last_seen_at - s.started_at)) / 60.0
            ), 1)                                                                       AS avg_min,
            ROUND(AVG(array_length(s.section_flow, 1)), 1)                             AS avg_depth
        FROM analytics_sessions s
        JOIN users u ON u.id = s.user_id
        GROUP BY u.role
        ORDER BY sessions DESC
    """)


def get_role_section_time():
    """Average seconds per section broken down by role — feeds the role × section heatmap."""
    return _query("""
        SELECT
            u.role::text                                         AS role,
            e.section,
            ROUND(AVG(e.time_spent_ms) / 1000.0, 1)             AS avg_sec,
            COUNT(*)                                             AS visits
        FROM analytics_events e
        JOIN analytics_sessions s ON s.session_id = e.session_id
        JOIN users u ON u.id = s.user_id
        WHERE e.event = 'section_exit'
          AND e.time_spent_ms IS NOT NULL
        GROUP BY u.role, e.section
        ORDER BY u.role, avg_sec DESC
    """)


def get_role_depth():
    """Session path depth distribution broken down by role."""
    return _query("""
        SELECT
            u.role::text                          AS role,
            array_length(s.section_flow, 1)       AS depth,
            COUNT(*)                               AS sessions
        FROM analytics_sessions s
        JOIN users u ON u.id = s.user_id
        WHERE array_length(s.section_flow, 1) IS NOT NULL
        GROUP BY u.role, depth
        ORDER BY u.role, depth
    """)


def get_kpis():
    row = _query("""
        SELECT
          (SELECT COUNT(*)
           FROM analytics_sessions)                                              AS total_sessions,
          (SELECT COUNT(DISTINCT user_id)
           FROM analytics_sessions
           WHERE user_id IS NOT NULL)                                            AS unique_users,
          (SELECT section
           FROM analytics_events
           WHERE event = 'section_enter'
           GROUP BY section
           ORDER BY COUNT(*) DESC
           LIMIT 1)                                                              AS top_section,
          (SELECT ROUND(AVG(session_ms) / 60000.0, 1)
           FROM (
               SELECT SUM(time_spent_ms) AS session_ms
               FROM analytics_events
               WHERE event = 'section_exit' AND time_spent_ms IS NOT NULL
               GROUP BY session_id
           ) t)                                                                  AS avg_min
    """)
    return row.iloc[0].to_dict() if not row.empty else {}
