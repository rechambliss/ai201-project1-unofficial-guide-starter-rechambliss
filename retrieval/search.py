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


def search(query: str, collection: chromadb.Collection, model: SentenceTransformer) -> None:
    query_vec = model.encode([query])[0].tolist()

    results = collection.query(
        query_embeddings=[query_vec],
        n_results=TOP_K,
        include=["documents", "metadatas", "distances"],
    )

    metas     = results["metadatas"][0]
    distances = results["distances"][0]

    print(f"\n{'=' * 70}")
    print(f"QUERY: {query}")
    print(f"{'=' * 70}")

    for rank, (meta, dist) in enumerate(zip(metas, distances), start=1):
        print(f"\n[Result {rank}  |  distance: {dist:.4f}]")
        print(f"  title       : {meta['title']}")
        print(f"  source_type : {meta['source_type']}")
        print(f"  source      : {meta['source']}")
        print(f"  chunk_number: {meta['chunk_number']}")
        print(f"  text        :")
        print(meta.get("chunk_text", ""))
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
