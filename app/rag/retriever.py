import pickle
import faiss
from sentence_transformers import SentenceTransformer
from app.config import settings

INDEX_PATH = "data/faiss_index/index.faiss"
META_PATH = "data/faiss_index/meta.pkl"
_model = _index = _meta = None

def _load():
    global _model, _index, _meta
    if _model is None:
        _model = SentenceTransformer(settings.EMBEDDING_MODEL)
    if _index is None:
        _index = faiss.read_index(INDEX_PATH)
    if _meta is None:
        with open(META_PATH, "rb") as f:
            _meta = pickle.load(f)

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