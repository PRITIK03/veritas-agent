from app.utils.encoding import force_utf8_output

force_utf8_output()

from app.rag.ingest import build_index

if __name__ == "__main__":
    build_index()