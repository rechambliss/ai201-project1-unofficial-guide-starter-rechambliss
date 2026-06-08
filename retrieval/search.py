"""
retrieval/search.py

Queries the ChromaDB collection built by retrieval/build_index.py.

Usage:
    # Run all 5 evaluation-plan queries
    python retrieval/search.py

    # Run a single custom query
    python retrieval/search.py "your question here"
"""

import sys
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

PROJECT_ROOT    = Path(__file__).resolve().parent.parent
CHROMA_DIR      = PROJECT_ROOT / "data" / "chroma"
COLLECTION_NAME = "liberty_offcampus"
EMBED_MODEL     = "sentence-transformers/all-MiniLM-L6-v2"
TOP_K           = 5

# All 5 questions from the Evaluation Plan in planning.md
EVAL_QUERIES = [
    "I am a freshman at Liberty University and want to move off campus next spring. Am I automatically eligible to live off campus?",
    "I want to live off campus but I do not have a car. What transportation options could help me get to campus?",
    "What does The Oasis offer for Liberty students, and how much does it cost per bedroom?",
    "How does The Vue at College Square compare to The Oasis for a student who wants to be close to campus?",
    "What do student discussions say about living at The Oasis as a graduate student or older student?",
]


def get_collection() -> chromadb.Collection:
    if not CHROMA_DIR.exists():
        sys.exit(f"ERROR: {CHROMA_DIR} not found. Run retrieval/build_index.py first.")
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    try:
        return client.get_collection(COLLECTION_NAME)
    except Exception:
        sys.exit(f"ERROR: Collection '{COLLECTION_NAME}' not found. Run retrieval/build_index.py first.")


def retrieve(query: str, collection: chromadb.Collection, model: SentenceTransformer) -> list[dict]:
    """
    Embed query and return top-K results as a list of dicts with keys:
        text     — original chunk content (no metadata prefix)
        meta     — full metadata dict (title, source, source_type, filename, chunk_number, ...)
        distance — cosine distance (lower = more similar)
    """
    query_vec = model.encode([query])[0].tolist()
    results = collection.query(
        query_embeddings=[query_vec],
        n_results=TOP_K,
        include=["metadatas", "distances"],
    )
    chunks = []
    for meta, dist in zip(results["metadatas"][0], results["distances"][0]):
        chunks.append({
            "text": meta.get("chunk_text", ""),
            "meta": meta,
            "distance": dist,
        })
    return chunks


def search(query: str, collection: chromadb.Collection, model: SentenceTransformer) -> None:
    """Pretty-print retrieval results to the terminal."""
    chunks = retrieve(query, collection, model)

    print(f"\n{'=' * 70}")
    print(f"QUERY: {query}")
    print(f"{'=' * 70}")

    for rank, chunk in enumerate(chunks, start=1):
        meta = chunk["meta"]
        print(f"\n[Result {rank}  |  distance: {chunk['distance']:.4f}]")
        print(f"  title       : {meta['title']}")
        print(f"  source_type : {meta['source_type']}")
        print(f"  source      : {meta['source']}")
        print(f"  chunk_number: {meta['chunk_number']}")
        print(f"  text        :")
        print(chunk["text"])
        print(f"{'-' * 70}")


def main() -> None:
    collection = get_collection()
    model = SentenceTransformer(EMBED_MODEL)

    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        search(query, collection, model)
    else:
        label = "evaluation" if len(EVAL_QUERIES) > 1 else "query"
        print(f"Running {len(EVAL_QUERIES)} {label} queries from planning.md ...")
        for query in EVAL_QUERIES:
            search(query, collection, model)


if __name__ == "__main__":
    main()
