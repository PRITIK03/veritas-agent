import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB = os.getenv("POSTGRES_DB", "veritas_agent")
    POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")

    # If this model becomes unavailable, make a real test call (see verify_model_available()
    # in app/utils/llm.py) — don't trust list_models() alone, it doesn't reflect per-key
    # access. Check https://ai.google.dev/gemini-api/docs/models for current Flash model names.
    GEMINI_MODEL = "gemini-3.6-flash"
    OPENROUTER_FALLBACK_MODEL = "google/gemini-2.5-flash-lite:free"
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"

settings = Settings()
