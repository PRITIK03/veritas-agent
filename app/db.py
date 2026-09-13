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

def log_query(query, route, answer, sources, grounded,
              failure_reason, latency_ms, input_tokens,
              output_tokens, estimated_cost_usd):
    try:
        conn = get_connection()
        cur = conn.cursor()
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
        cur.close()
        conn.close()
    except Exception as e:
        print(f"⚠️ Failed to log query to Postgres: {e}")

def get_recent_logs(limit: int = 20):
    """Fetch most recent query log rows for the verification ledger."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
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
    cols = [d[0] for d in cur.description]
    rows = [dict(zip(cols, row)) for row in cur.fetchall()]
    cur.close()
    conn.close()
    return rows


def get_grounding_trend(limit: int = 30):
    """Return the last N rows as (created_at, grounded) for the sparkline."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT created_at, grounded
        FROM query_logs
        ORDER BY created_at DESC
        LIMIT %s
        """,
        (limit,),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    # Return oldest-first so the sparkline reads left→right
    return list(reversed(rows))


def get_cost_per_verified_answer():
    """Cost per *grounded* answer — a sharper metric than cost-per-query."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            COALESCE(
                SUM(estimated_cost_usd) FILTER (WHERE grounded = TRUE)
                / NULLIF(COUNT(*) FILTER (WHERE grounded = TRUE), 0),
                0
            ) AS cost_per_verified
        FROM query_logs
        """
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    return float(row[0]) if row else 0.0
    """Single-query aggregate summary over query_logs.

    Returns total counts, grounding success rate, latency/cost averages,
    total cost, and a per-route breakdown, using conditional aggregates plus
    a FILTER-based route count so the whole report is one round-trip.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            COUNT(*)                                                   AS total_queries,
            COALESCE(
                ROUND(
                    100.0 * COUNT(*) FILTER (WHERE grounded = TRUE)
                    / NULLIF(COUNT(*), 0),
                    2
                ),
                0
            )                                                          AS grounding_success_rate_pct,
            COALESCE(AVG(latency_ms), 0)                               AS avg_latency_ms,
            COALESCE(AVG(estimated_cost_usd), 0)                       AS avg_estimated_cost_usd,
            COALESCE(SUM(estimated_cost_usd), 0)                       AS total_estimated_cost_usd,
            COUNT(*) FILTER (WHERE route = 'rag')                      AS rag_count,
            COUNT(*) FILTER (WHERE route = 'web_search')               AS web_search_count
        FROM query_logs
        """
    )
    row = cur.fetchone()
    cur.close()
    conn.close()

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