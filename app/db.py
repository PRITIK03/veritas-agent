import psycopg2
import json
from app.config import settings


def get_connection():
    return psycopg2.connect(
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        dbname=settings.POSTGRES_DB,
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
    )


def _run_query(sql, params=None):
    """Open a connection, run a read query, return all rows. Always closes."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        try:
            cur.execute(sql, params or ())
            cols = [d[0] for d in cur.description] if cur.description else []
            rows = cur.fetchall()
        finally:
            cur.close()
    finally:
        conn.close()
    return cols, rows


_EMPTY_SUMMARY = {
    "total_queries": 0,
    "grounding_success_rate_pct": 0.0,
    "avg_latency_ms": 0.0,
    "avg_estimated_cost_usd": 0.0,
    "total_estimated_cost_usd": 0.0,
    "route_counts": {"rag": 0, "web_search": 0},
}


def log_query(query, route, answer, sources, grounded,
              failure_reason, latency_ms, input_tokens,
              output_tokens, estimated_cost_usd):
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                INSERT INTO query_logs
                (query, route, answer, sources, grounded, failure_reason,
                 latency_ms, input_tokens, output_tokens, estimated_cost_usd)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (query, route, answer, json.dumps(sources), grounded,
                 failure_reason, latency_ms, input_tokens, output_tokens,
                 estimated_cost_usd),
            )
            conn.commit()
        finally:
            cur.close()
    except Exception as e:
        print(f"⚠️ Failed to log query to Postgres: {e}")
    finally:
        if conn is not None:
            conn.close()


def get_analytics_summary():
    """Single-query aggregate summary over query_logs."""
    try:
        cols, rows = _run_query(
            """
            SELECT
                COUNT(*) AS total_queries,
                COALESCE(
                    ROUND(
                        100.0 * COUNT(*) FILTER (WHERE grounded = TRUE)
                        / NULLIF(COUNT(*), 0),
                        2
                    ),
                    0
                ) AS grounding_success_rate_pct,
                COALESCE(AVG(latency_ms), 0) AS avg_latency_ms,
                COALESCE(AVG(estimated_cost_usd), 0) AS avg_estimated_cost_usd,
                COALESCE(SUM(estimated_cost_usd), 0) AS total_estimated_cost_usd,
                COUNT(*) FILTER (WHERE route = 'rag') AS rag_count,
                COUNT(*) FILTER (WHERE route = 'web_search') AS web_search_count
            FROM query_logs
            """
        )
    except Exception as e:
        print(f"⚠️ Analytics summary unavailable (Postgres): {e}")
        return dict(_EMPTY_SUMMARY)

    row = rows[0] if rows else None
    if row is None:
        return dict(_EMPTY_SUMMARY)

    (
        total_queries,
        grounding_success_rate_pct,
        avg_latency_ms,
        avg_estimated_cost_usd,
        total_estimated_cost_usd,
        rag_count,
        web_search_count,
    ) = row

    return {
        "total_queries": int(total_queries),
        "grounding_success_rate_pct": float(grounding_success_rate_pct),
        "avg_latency_ms": float(avg_latency_ms),
        "avg_estimated_cost_usd": float(avg_estimated_cost_usd),
        "total_estimated_cost_usd": float(total_estimated_cost_usd),
        "route_counts": {
            "rag": int(rag_count),
            "web_search": int(web_search_count),
        },
    }


def get_recent_queries(limit: int = 20):
    """Most recent N queries, newest first, for the history panel."""
    try:
        cols, rows = _run_query(
            """
            SELECT query, route, grounded, failure_reason,
                   latency_ms, estimated_cost_usd, created_at
            FROM query_logs
            ORDER BY created_at DESC
            LIMIT %s
            """,
            (limit,),
        )
    except Exception as e:
        print(f"⚠️ Recent-queries fetch unavailable (Postgres): {e}")
        return []
    return [dict(zip(cols, row)) for row in rows]


def get_cost_and_grounding_trend(limit: int = 30):
    """Last N queries (chronological) with cost and grounded status."""
    try:
        cols, rows = _run_query(
            """
            SELECT created_at, estimated_cost_usd, grounded
            FROM (
                SELECT created_at, estimated_cost_usd, grounded
                FROM query_logs
                ORDER BY created_at DESC
                LIMIT %s
            ) recent
            ORDER BY created_at ASC
            """,
            (limit,),
        )
    except Exception as e:
        print(f"⚠️ Trend fetch unavailable (Postgres): {e}")
        return []
    return [dict(zip(cols, row)) for row in rows]


def get_recent_logs(limit: int = 20):
    """Fetch most recent query log rows for the verification ledger."""
    cols, rows = _run_query(
        """
        SELECT id, created_at, query, route, grounded, failure_reason,
               latency_ms, input_tokens, output_tokens, estimated_cost_usd,
               answer, sources
        FROM query_logs
        ORDER BY created_at DESC
        LIMIT %s
        """,
        (limit,),
    )
    return [dict(zip(cols, row)) for row in rows]


def get_grounding_trend(limit: int = 30):
    """Return the last N rows as (created_at, grounded) for the sparkline."""
    cols, rows = _run_query(
        """
        SELECT created_at, grounded
        FROM query_logs
        ORDER BY created_at DESC
        LIMIT %s
        """,
        (limit,),
    )
    return list(reversed(rows))


def get_cost_per_verified_answer():
    """Cost per grounded answer."""
    cols, rows = _run_query(
        """
        SELECT COALESCE(
            SUM(estimated_cost_usd) FILTER (WHERE grounded = TRUE)
            / NULLIF(COUNT(*) FILTER (WHERE grounded = TRUE), 0),
            0
        ) AS cost_per_verified
        FROM query_logs
        """
    )
    return float(rows[0][0]) if rows else 0.0
