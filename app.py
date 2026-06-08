"""
app.py

Gradio web interface for the Liberty University Off-Campus Housing Guide.

Shared resources (ChromaDB collection, embedding model, Groq client) are
loaded once at startup and reused for every query.

Run:
    python app.py
"""

import os
import sys
from pathlib import Path

import gradio as gr
from dotenv import load_dotenv
from groq import Groq
from sentence_transformers import SentenceTransformer

# Project root is the directory containing this file, so sibling packages
# (retrieval/, generation/) are importable without sys.path changes.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from generation.answer import answer, build_sources
from retrieval.search import get_collection

load_dotenv()

# ---------------------------------------------------------------------------
# Startup — load shared resources once
# ---------------------------------------------------------------------------

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    sys.exit("ERROR: GROQ_API_KEY not set. Add it to your .env file.")

_collection = get_collection()
_model      = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
_groq       = Groq(api_key=api_key)

# ---------------------------------------------------------------------------
# Gradio handler
# ---------------------------------------------------------------------------

def format_sources_md(sources: list[dict]) -> str:
    """Render source list as Markdown for display in the UI."""
    if not sources:
        return "_No sources retrieved._"
    lines = []
    for s in sources:
        chunks_str = ", ".join(str(n) for n in s["chunk_numbers"])
        lines.append(
            f"**{s['label']} — {s['title']}**  \n"
            f"Type: `{s['source_type']}`  \n"
            f"URL: {s['source']}  \n"
            f"File: `{s['filename']}` — chunk(s) {chunks_str}"
        )
    return "\n\n".join(lines)


def handle_query(question: str) -> tuple[str, str]:
    question = question.strip()
    if not question:
        return "Please enter a question.", ""
    try:
        ans, sources = answer(question, _collection, _model, _groq)
        return ans, format_sources_md(sources)
    except Exception as e:
        return f"Error: {e}", ""


# ---------------------------------------------------------------------------
# Gradio UI
# ---------------------------------------------------------------------------

with gr.Blocks(title="LU Off-Campus Housing Guide") as demo:

    gr.Markdown("# Liberty University Off-Campus Housing Guide")
    gr.Markdown(
        "Ask questions about off-campus eligibility, housing options, "
        "transportation, and student experiences. "
        "Answers are grounded in collected source documents only."
    )

    question_box = gr.Textbox(
        label="Your question",
        placeholder="e.g. What does The Oasis offer for Liberty students?",
        lines=2,
    )

    submit_btn = gr.Button("Ask", variant="primary")

    with gr.Column():
        gr.Markdown("### Answer")
        answer_box = gr.Textbox(lines=10, interactive=False, show_label=False)

    with gr.Column():
        gr.Markdown("### Sources")
        sources_box = gr.Markdown()

    # Submit on button click or Enter keypress in the textbox
    submit_btn.click(
        fn=handle_query,
        inputs=question_box,
        outputs=[answer_box, sources_box],
    )
    question_box.submit(
        fn=handle_query,
        inputs=question_box,
        outputs=[answer_box, sources_box],
    )


if __name__ == "__main__":
    demo.launch()
