"""
ingest/chunk.py

Loads .txt and .pdf files from data/raw/, strips the structured header
block into metadata, cleans the body text, applies recursive token-aware
chunking, and writes every chunk to data/processed/chunks.jsonl.

Run from the project root:
    python ingest/chunk.py
"""

import json
import re
import sys
from pathlib import Path

import pdfplumber
from langchain_text_splitters import RecursiveCharacterTextSplitter

# ---------------------------------------------------------------------------
# Paths and tuning constants
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "documents"
OUT_DIR = PROJECT_ROOT / "data" / "processed"
OUT_FILE = OUT_DIR / "chunks.jsonl"

CHUNK_SIZE = 250      # tokens  (matches planning.md architecture spec)
CHUNK_OVERLAP = 50    # tokens

# Keys recognised in the top header block of every .txt source file.
# Any other KEY: value line is treated as body content.
_HEADER_KEYS = {"SOURCE", "SOURCE_TYPE", "TITLE"}

# ---------------------------------------------------------------------------
# Boilerplate patterns to remove before chunking
# ---------------------------------------------------------------------------

_BOILERPLATE = re.compile(
    r"(skip to (?:main )?content"
    r"|back to top"
    r"|all rights reserved"
    r"|cookie\s*(?:policy|settings)"
    r"|privacy\s*policy"
    r"|terms of use"
    r"|©\s*\d{4}"
    r"|\bshare this\b|\bprint this\b|\btweet\b"
    r"|posted by u/\S+"
    r"|^\d+\s*(?:points?|upvotes?|comments?|awards?)\s*$"
    r"|^\s*\[deleted\]\s*$"
    r"|^\s*\[removed\]\s*$"
    r"|REMINDER:.*?(?=\n\n|\Z)"
    r"|^\s*CONTENT:\s*$"                          # Reddit file section label
    r"|r/\w+\s*•\s*\d+[ydhm]\s*ago"              # subreddit + relative timestamp
    r"|\b\w+\s*•\s*\d+[ydhm]\s*ago"              # username + relative timestamp
    r"|^\s*\w{3,20}\s*$(?=\n\S))",               # bare username lines; ) closes capture group
    re.IGNORECASE | re.MULTILINE | re.DOTALL,
)

# ---------------------------------------------------------------------------
# Header parsing
# ---------------------------------------------------------------------------

def _parse_headers(raw: str) -> tuple[dict, str]:
    """
    Reads the leading KEY: value header block from raw text.

    Stops at the first blank line after seeing at least one recognised header,
    or at the first non-header line. Everything after the header block is the
    body. Returns (meta_dict, body_text).
    """
    meta: dict[str, str] = {}
    lines = raw.splitlines()
    body_start = 0

    for i, line in enumerate(lines):
        stripped = line.strip()

        if not stripped:
            if meta:
                # Blank line signals end of header block
                body_start = i + 1
                break
            # Leading blank line before any header — skip it
            body_start = i + 1
            continue

        colon_pos = stripped.find(":")
        if colon_pos > 0:
            key = stripped[:colon_pos].strip().upper()
            if key in _HEADER_KEYS:
                meta[key] = stripped[colon_pos + 1:].strip()
                body_start = i + 1
                continue

        # Line is not a recognised header — body starts here
        body_start = i
        break

    return meta, "\n".join(lines[body_start:])

# ---------------------------------------------------------------------------
# Text cleaning
# ---------------------------------------------------------------------------

def _clean(text: str, title: str = "") -> str:
    """Remove boilerplate, normalise whitespace, collapse blank lines."""
    text = _BOILERPLATE.sub("", text)
    # Drop the first line if it just repeats the document title
    if title:
        lines = text.lstrip().splitlines()
        if lines and lines[0].strip().lower() == title.strip().lower():
            text = "\n".join(lines[1:])
    text = re.sub(r"[ \t]+", " ", text)            # inline whitespace → single space
    text = re.sub(r"^ | $", "", text, flags=re.MULTILINE)  # strip per-line padding
    text = re.sub(r"\n{3,}", "\n\n", text)         # max one blank line between blocks
    return text.strip()

# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------

def _load_txt(path: Path) -> tuple[dict, str]:
    raw = path.read_text(encoding="utf-8")
    meta, body = _parse_headers(raw)
    meta.setdefault("TITLE", path.stem.replace("_", " ").title())
    meta.setdefault("SOURCE", "")
    meta.setdefault("SOURCE_TYPE", "unknown")
    return meta, body


def _load_pdf(path: Path) -> tuple[dict, str]:
    pages: list[str] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            pages.append(page.extract_text() or "")
    raw = "\n\n".join(pages)

    meta, body = _parse_headers(raw)

    # Fall back to filename-derived values when the PDF has no header block
    if not meta.get("TITLE"):
        meta["TITLE"] = path.stem.replace("_", " ").title()
    if not meta.get("SOURCE"):
        meta["SOURCE"] = ""
    if not meta.get("SOURCE_TYPE"):
        name = path.stem.lower()
        meta["SOURCE_TYPE"] = "reddit_pdf" if "reddit" in name else "pdf_document"

    return meta, body

# ---------------------------------------------------------------------------
# Per-file pipeline
# ---------------------------------------------------------------------------

def _process(path: Path, splitter: RecursiveCharacterTextSplitter) -> list[dict]:
    suffix = path.suffix.lower()
    if suffix == ".txt":
        meta, body = _load_txt(path)
    elif suffix == ".pdf":
        meta, body = _load_pdf(path)
    else:
        return []

    body = _clean(body, title=meta.get("TITLE", ""))
    if not body:
        print(f"  [SKIP] {path.name} — no content after cleaning", file=sys.stderr)
        return []

    return [
        {
            "text": chunk_text,
            "metadata": {
                "title": meta["TITLE"],
                "source": meta["SOURCE"],
                "source_type": meta["SOURCE_TYPE"],
                "url": meta["SOURCE"],   # SOURCE holds the URL in this corpus
                "filename": path.name,
                "chunk_number": i,
            },
        }
        for i, chunk_text in enumerate(splitter.split_text(body))
    ]

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    if not RAW_DIR.exists():
        sys.exit(f"ERROR: {RAW_DIR} does not exist. Add source files and re-run.")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        encoding_name="cl100k_base",
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    files = sorted(RAW_DIR.glob("*.txt")) + sorted(RAW_DIR.glob("*.pdf"))
    if not files:
        sys.exit(f"No .txt or .pdf files found in {RAW_DIR}")

    all_chunks: list[dict] = []
    for path in files:
        chunks = _process(path, splitter)
        print(f"  {path.name}: {len(chunks)} chunks")
        all_chunks.extend(chunks)

    with OUT_FILE.open("w", encoding="utf-8") as f:
        for chunk in all_chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")

    total = len(all_chunks)
    print(f"\nTotal: {total} chunks  →  {OUT_FILE}\n")

    # 5 evenly-spaced samples drawn from across the full output
    if total == 0:
        print("No chunks produced.")
        return

    indices = (
        [int(i * (total - 1) / 4) for i in range(5)]
        if total >= 5
        else list(range(total))
    )

    print("=" * 60)
    print("SAMPLE CHUNKS")
    print("=" * 60)
    for idx in indices:
        c = all_chunks[idx]
        m = c["metadata"]
        print(f"\n[Chunk {idx}]")
        print(f"  title       : {m['title']}")
        print(f"  source_type : {m['source_type']}")
        print(f"  source      : {m['source']}")
        print(f"  filename    : {m['filename']}")
        print(f"  chunk_number: {m['chunk_number']}")
        print(f"  text        :\n{c['text']}")
        print("-" * 60)


if __name__ == "__main__":
    main()
