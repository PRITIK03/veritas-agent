import os
import pickle
import faiss
from sentence_transformers import SentenceTransformer
from app.config import settings

DOCS_DIR = "data/docs"
INDEX_PATH = "data/faiss_index/index.faiss"
META_PATH = "data/faiss_index/meta.pkl"
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
    os.makedirs("data/faiss_index", exist_ok=True)
    model = SentenceTransformer(settings.EMBEDDING_MODEL)

    all_chunks, all_sources = [], []
    for filename in os.listdir(DOCS_DIR):
        if not filename.endswith(".txt"):
            continue
        with open(os.path.join(DOCS_DIR, filename), "r", encoding="utf-8") as f:
            text = f.read()
        for i, chunk in enumerate(chunk_text(text)):
            all_chunks.append(chunk)
            all_sources.append({"file": filename, "chunk_id": i})

    if not all_chunks:
        raise ValueError(f"No .txt files found in {DOCS_DIR}. Add some docs first.")

    embeddings = model.encode(all_chunks, show_progress_bar=True)
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)

    faiss.write_index(index, INDEX_PATH)
    with open(META_PATH, "wb") as f:
        pickle.dump({"chunks": all_chunks, "sources": all_sources}, f)

    print(f"✅ Indexed {len(all_chunks)} chunks from {DOCS_DIR}")

if __name__ == "__main__":
    build_index()