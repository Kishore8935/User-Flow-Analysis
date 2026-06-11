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
          (SELECT ROUND(
             AVG(EXTRACT(EPOCH FROM (last_seen_at - started_at)) / 60.0), 1
           ) FROM analytics_sessions)                                            AS avg_min
    """)
    return row.iloc[0].to_dict() if not row.empty else {}
