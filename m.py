"""
Flask web app for the finance chatbot: serves the chat UI and exposes
a small JSON API that calls a modular external LangGraph state machine.
"""

import json
import logging
import uuid
from flask import Flask, abort, jsonify, render_template, request, send_from_directory

# Configurations, Location Helpers, and Modular Graph Import
from src import config
from src.rag_chain import format_location, graph_agent
from langchain_core.messages import HumanMessage

FINANCE_DIR = config.PROJECT_ROOT.parent / "Finance"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)

TOP_CATEGORY_COUNT = 6
SUGGESTIONS_LIMIT = 12
QUESTIONS_PER_CATEGORY = 3
MAX_SUGGESTED_QUESTION_LENGTH = 100

def _load_faq_index() -> list[dict]:
    if not config.RAW_DOCUMENTS_PATH.exists():
        logger.warning("raw_documents.jsonl not found - run the ingestion pipeline first.")
        return []
    entries = []
    with config.RAW_DOCUMENTS_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                doc = json.loads(line)
                metadata = doc.get("metadata") or {}
                question = metadata.get("question") or doc.get("text", "")[:60]
                if not question or len(str(question)) > MAX_SUGGESTED_QUESTION_LENGTH:
                    continue
                entries.append({
                    "question": str(question),
                    "category": metadata.get("category") or "General",
                    "source": metadata.get("source") or "",
                })
            except Exception:
                continue
    return entries

FAQ_INDEX = _load_faq_index()

def _format_sources(sources: list[dict]) -> list[dict]:
    formatted = []
    for chunk in sources:
        metadata = chunk.get("metadata", {})
        formatted.append({
            "source": metadata.get("source"),
            "file_type": metadata.get("file_type"),
            "page": metadata.get("page"),
            "location": format_location(metadata),
            "snippet": chunk.get("text", "")[:220],
            "score": round(chunk.get("score", 0.0), 4) if chunk.get("score") else 0.0
        })
    return formatted

# --------------------------------------------------------------------------
# Clean Flask Endpoint Interface Mappings
# --------------------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/categories")
def get_categories():
    counts = {}
    for entry in FAQ_INDEX:
        cat_name = str(entry.get("category", "General")).strip()
        if not cat_name or cat_name.lower() == "general":
            continue
        counts[cat_name] = counts.get(cat_name, 0) + 1
    top = sorted(counts.items(), key=lambda kv: kv, reverse=True)[:TOP_CATEGORY_COUNT]
    return jsonify([{"category": name, "count": count} for name, count in top])

@app.route("/api/categories/<category>/questions")
def get_category_questions(category: str):
    matches = [e["question"] for e in FAQ_INDEX if str(e.get("category")).lower() == category.lower()]
    return jsonify(matches[:QUESTIONS_PER_CATEGORY])

@app.route("/api/suggestions")
def get_suggestions():
    query = request.args.get("q", "").strip().lower()
    if len(query) < 2:
        return jsonify([])
    matches = [e["question"] for e in FAQ_INDEX if query in str(e.get("question")).lower()]
    return jsonify(matches[:SUGGESTIONS_LIMIT])

@app.route("/api/session", methods=["POST"])
def start_session():
    body = request.get_json(force=True) or {}
    conversation_id = body.get("conversation_id", "default_thread")
    return jsonify({"conversation_id": conversation_id})

@app.route("/api/ask", methods=["POST"])
def ask():
    body = request.get_json(force=True) or {}
    question = body.get("question", "").strip()
    conversation_id = body.get("conversation_id", "default_thread")
    
    if not question:
        return jsonify({"error": "question is required"}), 400

    config_thread = {"configurable": {"thread_id": conversation_id}}
    initial_state = {"messages": [HumanMessage(content=question)]}
    
    try:
        # Invoking the modular external agent graph cleanly
        output_state = graph_agent.invoke(initial_state, config=config_thread)
        last_ai_message = output_state["messages"][-1].content
        payload_data = output_state.get("final_payload", {})
        raw_sources = payload_data.get("sources", [])
    except Exception as e:
        logger.error(f"Graph invocation error: {str(e)}")
        return jsonify({
            "answer": "An internal graph execution error occurred. Please try again.",
            "method": "Error Fallback",
            "sources": [],
            "conversation_id": conversation_id
        })
    
    mock_msg_id = f"msg_{uuid.uuid4().hex[:8]}"
    return jsonify({
        "answer": last_ai_message,
        "method": payload_data.get("method", "RAG Pipeline (Azure OpenAI Synth)"),
        "sources": _format_sources(raw_sources),
        "conversation_id": conversation_id,
        "message_id": mock_msg_id
    })

@app.route("/source/<path:filename>")
def serve_source(filename: str):
    if not (FINANCE_DIR / filename).resolve().is_relative_to(FINANCE_DIR.resolve()):
        abort(404)
    is_pdf = filename.lower().endswith(".pdf")
    return send_from_directory(FINANCE_DIR, filename, as_attachment=not is_pdf)

@app.route("/api/feedback", methods=["POST"])
def feedback():
    body = request.get_json(force=True) or {}
    message_id = body.get("message_id")
    if not message_id:
        return jsonify({"error": "message_id is required"}), 400
    return jsonify({"ok": True})

if __name__ == "__main__":
    logger.info("Loaded %d FAQ entries for categories/suggestions", len(FAQ_INDEX))
    app.run(debug=True, use_reloader=False, port=5000)
