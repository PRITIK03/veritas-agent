CREATE TABLE IF NOT EXISTS query_logs (
    id SERIAL PRIMARY KEY,
    query TEXT NOT NULL,
    route TEXT NOT NULL,              -- 'rag' or 'web_search'
    answer TEXT,
    sources JSONB,
    grounded BOOLEAN,
    failure_reason TEXT,
    latency_ms INTEGER,
    input_tokens INTEGER,
    output_tokens INTEGER,
    estimated_cost_usd NUMERIC(10, 6),
    created_at TIMESTAMP DEFAULT NOW()
);