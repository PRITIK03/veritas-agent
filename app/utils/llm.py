import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

import requests
from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import settings

LLM_TIMEOUT_SECONDS = 20
LLM_TIMEOUT_MESSAGE = f"LLM call exceeded {LLM_TIMEOUT_SECONDS}s timeout"

_gemini = None

def get_gemini():
    global _gemini
    if _gemini is None:
        _gemini = ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL,
            google_api_key=settings.GEMINI_API_KEY,
        )
    return _gemini

_RATE_LIMIT_MARKERS = ("429", "resource_exhausted", "rate limit", "rate_limit", "quota")


def _is_rate_limit_error(exc: Exception) -> bool:
    text = f"{type(exc).__name__}: {exc}".lower()
    return any(marker in text for marker in _RATE_LIMIT_MARKERS)


def _invoke_with_timeout(prompt: str, timeout: float = LLM_TIMEOUT_SECONDS) -> str:
    """Single Gemini call with a hard timeout so no request can hang forever."""
    llm = get_gemini()
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(llm.invoke, prompt)
        try:
            response = future.result(timeout=timeout)
        except FuturesTimeoutError:
            raise TimeoutError(LLM_TIMEOUT_MESSAGE) from None
    return _extract_text(response)


def invoke_with_retry(prompt: str, max_retries: int = 2, base_delay: float = 2.0,
                       timeout: float = LLM_TIMEOUT_SECONDS) -> str:
    """Transport-level retry for transient Gemini rate-limit (429) failures.

    This is deliberately separate from any answer-quality retry loop: it only
    retries when the API call itself fails with a rate-limit error, up to
    max_retries additional attempts with linear backoff. Non-rate-limit errors
    propagate immediately. The response cache wraps this, so a successful retry
    is cached normally and a hit never reaches here.
    """
    attempt = 0
    while True:
        try:
            return _invoke_with_timeout(prompt, timeout=timeout)
        except TimeoutError:
            raise
        except Exception as e:
            if not _is_rate_limit_error(e) or attempt >= max_retries:
                raise
            attempt += 1
            delay = base_delay * attempt
            print(f"⏳ Gemini rate-limited — retrying in {delay:.0f}s (attempt {attempt + 1}/{max_retries + 1})")
            time.sleep(delay)

def verify_model_available():
    """Make a real one-token test call to confirm the configured model is actually
    callable with this API key. list_models() is NOT sufficient — it returns models
    that exist in Google's catalog but doesn't reflect per-key/per-project permissions.
    Call this once at startup only; don't call it per-node to avoid burning API quota.

    A transient 429/rate-limit is NOT a configuration problem — it degrades to a warning.
    Only 404/403/model-not-found errors raise the hard RuntimeError.
    """
    from google import genai as google_genai

    configured = settings.GEMINI_MODEL
    client = google_genai.Client(api_key=settings.GEMINI_API_KEY)
    try:
        client.models.generate_content(model=configured, contents="hi")
        print(f"✅ Model '{configured}' confirmed callable.")
    except Exception as e:
        if _is_rate_limit_error(e):
            print(f"⚠️ Gemini quota exhausted for today — model is likely fine, this is a rate limit, "
                  f"not a configuration problem. Server will still start; live queries may fail until quota resets.")
        else:
            print(f"❌ Model '{configured}' call failed.\n   API error: {e}")
            raise RuntimeError(
                f"Configured model '{configured}' is not usable with this API key.\n"
                f"Check https://ai.google.dev/gemini-api/docs/models for a current alternative\n"
                f"and update GEMINI_MODEL in app/config.py."
            ) from e

def _extract_text(response) -> str:
    """Safely extract string content from a LangChain LLM response.
    Newer langchain-google-genai versions may return response.content as a
    list of content blocks rather than a plain string."""
    content = response.content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                parts.append(block.get("text", ""))
            else:
                parts.append(str(block))
        return "".join(parts).strip()
    return str(content).strip()

def call_openrouter(prompt: str, model: str = None) -> str:
    """Fallback/secondary LLM path via OpenRouter — used if you want the
    specialist agent on a different provider than the router."""
    model = model or settings.OPENROUTER_FALLBACK_MODEL
    headers = {"Authorization": f"Bearer {settings.OPENROUTER_API_KEY}"}
    payload = {"model": model, "messages": [{"role": "user", "content": prompt}]}
    resp = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers, json=payload, timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]
