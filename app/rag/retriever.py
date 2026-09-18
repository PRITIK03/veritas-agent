import os
import pickle
import threading

import faiss
from sentence_transformers import SentenceTransformer

from app.config import settings

# Resolved relative to the project root (two levels up from this file), so the
# server works regardless of the directory it was launched from.
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INDEX_PATH = os.path.join(ROOT_DIR, "data", "faiss_index", "index.faiss")
META_PATH = os.path.join(ROOT_DIR, "data", "faiss_index", "meta.pkl")

_model = _index = _meta = None
_load_lock = threading.Lock()
_warmed_up = False


def _load():
    global _model, _index, _meta
    if _model is not None and _index is not None and _meta is not None:
        return
    with _load_lock:
        if _model is None:
            _model = SentenceTransformer(settings.EMBEDDING_MODEL)
        if _index is None:
            _index = faiss.read_index(INDEX_PATH)
        if _meta is None:
            with open(META_PATH, "rb") as f:
                _meta = pickle.load(f)


def warmup():
    """Eagerly load the embedding model + FAISS index and run one encode.

    Called once at server startup so the first user query doesn't pay the
    multi-second cold-start cost (which previously looked like a 'hang' to
    HTTP clients with short timeouts).
    """
    global _warmed_up
    if _warmed_up:
        return
    _load()
    _model.encode(["warmup"])
    _warmed_up = True
    print(f"✅ RAG index warmed up ({_index.ntotal} vectors, model={settings.EMBEDDING_MODEL})")


def retrieve(query: str, k: int = 3):
    _load()
    query_vec = _model.encode([query])
    distances, indices = _index.search(query_vec, k)
    results = []
    for idx, dist in zip(indices[0], distances[0]):
        if idx == -1:
            continue
        results.append({
            "text": _meta["chunks"][idx],
            "source": _meta["sources"][idx],
            "distance": float(dist),
        })
    return results