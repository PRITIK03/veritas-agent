"""
Simple JSON file cache for LLM responses — dev/testing only.

Keyed by sha256(prompt). Stored at data/llm_cache.json.
Purpose: avoid burning the 20 req/day Gemini free-tier quota on repeated
identical prompts during iterative local testing. Has zero effect on
correctness — a cache miss always falls through to a real API call.

To clear the cache: delete data/llm_cache.json (or call clear_cache()).
To disable: set LLM_CACHE_ENABLED=false in your .env.
"""

import hashlib
import json
import os
import threading
from pathlib import Path

from app.utils.llm import invoke_with_retry

# data/ at the project root (three levels up from this file) — NOT app/data/.
CACHE_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "llm_cache.json"
CACHE_ENABLED = os.getenv("LLM_CACHE_ENABLED", "true").lower() != "false"

# Guards against two concurrent requests (or cache threads) interleaving a
# read-modify-write of the JSON file and silently dropping an entry.
_lock = threading.Lock()


def _load() -> dict:
    if CACHE_PATH.exists():
        try:
            with open(CACHE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            # Corrupt/unreadable cache must never crash a request — start fresh.
            print(f"⚠️ Cache file unreadable ({e}) — starting with an empty cache.")
            return {}
    return {}


def _save(cache: dict) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = CACHE_PATH.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2)
    os.replace(tmp, CACHE_PATH)  # atomic — no torn writes if interrupted


def _key(prompt: str) -> str:
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


def cached_llm_invoke(prompt: str, timeout: float = 20.0) -> str:
    """Call the LLM with prompt, returning cached text if available.

    Returns the plain text response string (already extracted).
    Prints a clear status line on every call so cache hits are never silent.
    The underlying Gemini call carries a hard timeout (default 20s) via
    invoke_with_retry, so a cache miss can raise TimeoutError instead of
    hanging indefinitely.
    """
    if not CACHE_ENABLED:
        return invoke_with_retry(prompt, timeout=timeout)

    k = _key(prompt)
    with _lock:
        cache = _load()
        if k in cache:
            print(f"💾 Cache hit — skipping API call (key={k[:12]}...)")
            return cache[k]

    # Miss — call the API outside the lock so concurrent different prompts
    # don't serialize on the network call.
    print(f"🌐 Cache miss — calling API (key={k[:12]}...)")
    text = invoke_with_retry(prompt, timeout=timeout)

    with _lock:
        cache = _load()  # re-read: another thread may have written meanwhile
        cache[k] = text
        _save(cache)
    return text


def clear_cache() -> None:
    """Delete the on-disk cache file."""
    if CACHE_PATH.exists():
        CACHE_PATH.unlink()
        print(f"🗑️  Cache cleared: {CACHE_PATH}")
    else:
        print("Cache file does not exist — nothing to clear.")
