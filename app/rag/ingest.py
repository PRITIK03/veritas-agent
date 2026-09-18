import os
import pickle

import faiss
from sentence_transformers import SentenceTransformer

from app.config import settings

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DOCS_DIR = os.path.join(ROOT_DIR, "data", "docs")
INDEX_DIR = os.path.join(ROOT_DIR, "data", "faiss_index")
INDEX_PATH = os.path.join(INDEX_DIR, "index.faiss")
META_PATH = os.path.join(INDEX_DIR, "meta.pkl")
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks

def build_index():
    os.makedirs(INDEX_DIR, exist_ok=True)
    model = SentenceTransformer(settings.EMBEDDING_MODEL)

    # Read every file once — no handle leaks, deterministic order.
    file_chunks = {}
    for filename in sorted(os.listdir(DOCS_DIR)):
        if not filename.endswith(".txt"):
            continue
        with open(os.path.join(DOCS_DIR, filename), "r", encoding="utf-8") as f:
            file_chunks[filename] = chunk_text(f.read())

    all_chunks, all_sources = [], []
    for filename, chunks in file_chunks.items():
        if not chunks:
            print(f"⚠️ {filename} produced zero chunks (empty or unreadable) — skipped.")
            continue
        for i, chunk in enumerate(chunks):
            all_chunks.append(chunk)
            all_sources.append({"file": filename, "chunk_id": i})

    if not all_chunks:
        raise ValueError(f"No usable .txt content found in {DOCS_DIR}. Add some docs first.")

    embeddings = model.encode(all_chunks, show_progress_bar=True)
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)

    faiss.write_index(index, INDEX_PATH)
    with open(META_PATH, "wb") as f:
        pickle.dump({"chunks": all_chunks, "sources": all_sources}, f)

    print(f"✅ Indexed {len(all_chunks)} chunks from {len(file_chunks)} files in {DOCS_DIR}")

if __name__ == "__main__":
    build_index()