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