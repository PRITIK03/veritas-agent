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

def get_analytics_summary():
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