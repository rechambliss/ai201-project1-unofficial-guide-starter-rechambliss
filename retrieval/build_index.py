"""
retrieval/build_index.py

Embeds all chunks from data/processed/chunks.jsonl using
sentence-transformers/all-MiniLM-L6-v2 and stores them in a persistent
ChromaDB collection at data/chroma.

The collection is dropped and rebuilt on every run so the index stays
in sync with chunks.jsonl during development.

Run from the project root:
    python retrieval/build_index.py
"""

import json
import sys
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHUNKS_FILE = PROJECT_ROOT / "data" / "processed" / "chunks.jsonl"
CHROMA_DIR  = PROJECT_ROOT / "data" / "chroma"

COLLECTION_NAME = "liberty_offcampus"
EMBED_MODEL     = "sentence-transformers/all-MiniLM-L6-v2"
BATCH_SIZE      = 64


def load_chunks(path: Path) -> list[dict]:
    chunks = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                chunks.append(json.loads(line))
    return chunks


def main() -> None:
    if not CHUNKS_FILE.exists():
        sys.exit(f"ERROR: {CHUNKS_FILE} not found. Run ingest/chunk.py first.")

    print(f"Loading chunks from {CHUNKS_FILE} ...")
    chunks = load_chunks(CHUNKS_FILE)
    print(f"  {len(chunks)} chunks loaded")

    print(f"\nLoading embedding model: {EMBED_MODEL} ...")
    model = SentenceTransformer(EMBED_MODEL)

    # Build metadata-enriched text for embedding so the vector space
    # reflects source type and title context, not just raw content.
    def make_embedding_text(c: dict) -> str:
        m = c["metadata"]
        return (
            f"Title: {m['title']}\n"
            f"Source Type: {m['source_type']}\n"
            f"Source: {m['source']}\n"
            f"Content:\n{c['text']}"
        )

    embedding_texts = [make_embedding_text(c) for c in chunks]
    print(f"Embedding {len(embedding_texts)} chunks ...")
    embeddings = model.encode(embedding_texts, batch_size=BATCH_SIZE, show_progress_bar=True)

    print(f"\nConnecting to ChromaDB at {CHROMA_DIR} ...")
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    # Always drop and recreate — old vectors are never reused
    try:
        client.delete_collection(COLLECTION_NAME)
        print(f"  Dropped existing collection '{COLLECTION_NAME}'")
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )
    print(f"  Created collection '{COLLECTION_NAME}'")

    # Stable chunk ID: filename + chunk number
    ids = [f"{c['metadata']['filename']}_chunk_{c['metadata']['chunk_number']}" for c in chunks]

    # Preserve original chunk text in metadata so search.py can display it
    # cleanly, separate from the metadata-prefixed embedding document.
    metadatas = [
        {**c["metadata"], "chunk_text": c["text"]}
        for c in chunks
    ]

    for start in range(0, len(chunks), BATCH_SIZE):
        end = min(start + BATCH_SIZE, len(chunks))
        collection.add(
            ids=ids[start:end],
            embeddings=embeddings[start:end].tolist(),
            documents=embedding_texts[start:end],
            metadatas=metadatas[start:end],
        )

    print(f"\nDone. {collection.count()} vectors stored in '{COLLECTION_NAME}'")


if __name__ == "__main__":
    main()
