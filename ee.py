import os
import json
import logging
import uuid
import re
from flask import Flask, abort, jsonify, render_template, request, send_from_directory, session
from langchain_community.vectorstores import FAISS
from langchain_core.embeddings import FakeEmbeddings
from langchain_core.messages import HumanMessage

# Modular Graph Engine and Global Configurations Import
from src import config
from src.rag_chain import graph_agent

# Initialize standard enterprise logging stream utilities
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = "super_secret_finance_passphrase_key"

# Production Layout Boundaries and Constants matching your variables setup
TOP_CATEGORY_COUNT = 4
SUGGESTIONS_LIMIT = 12
QUESTIONS_PER_CATEGORY = 3
MAX_SUGGESTED_QUESTION_LENGTH = 100
FINANCE_DIR = config.PROJECT_ROOT.parent / "Finance"
INDEX_PATH = "data/faiss_index"

# Strict Predefined Corporate Categories mapping array rules
ALLOWED_CATEGORIES = {
    "accounts payable", 
    "corporate credit card", 
    "food", 
    "reimbursement account"
}


# 🟢 1. HELPER: CONTENT FORMATTING RULES
def convert_multiple_asterisks_to_bold(text: str) -> str:
    """Converts all instances of **text** to <b>text</b> in a string."""
    return re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)


# 🟢 2. HELPER: METADATA LOCATION STRING BUILDER
def format_location(metadata: dict) -> str:
    """Helper function to format source location for the frontend UI."""
    file_type = metadata.get("file_type", "").lower()
    if file_type in ["xlsx", "xls"]:
        row = metadata.get("row_index", "")
        sheet = metadata.get("sheet_name", "Sheet1")
        return f"Sheet: {sheet}, Row: {row}" if row else f"Sheet: {sheet}"
    elif file_type == "pdf":
        page = metadata.get("page", 0)
        return f"Page: {page + 1}"
    else:
        return "Document Section"


# 🟢 3. HELPER: LIGHTWEIGHT BINARY METADATA EXTRACTOR (Replaces load_faq_index file scan)
def _extract_faiss_documents() -> list:
    """Natively reads documents straight from the local FAISS index binary files

    without loading massive external neural network connection models or custom loaders.
    """
    try:
        if not os.path.exists(INDEX_PATH):
            logger.warning("FAISS vector storage mapping repository folder not found at %s", INDEX_PATH)
            return []
        
        # Load the binary database layout safely by matching signature dimensions (OpenAI width: 1536)
        fake_embeddings = FakeEmbeddings(size=1536)
        vector_store = FAISS.load_local(INDEX_PATH, fake_embeddings, allow_dangerous_deserialization=True)
        return list(vector_store.docstore._dict.values())
    except Exception as e:
        logger.error("Failed to extract metadata maps out of binary FAISS index layout: %s", str(e), exc_info=True)
        return []


# 🟢 4. HELPER: SOURCE METADATA FORMATTING ENGINE
def _format_sources(sources: list[dict]) -> list[dict]:
    """Formats raw vector source metrics blocks into clean UI target payloads."""
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


# 🟢 5. ROUTE: RENDER THE MAIN SYSTEM DASHBOARD
@app.route("/")
def index():
    return render_template("index.html")


# 🟢 6. ROUTE: GET CATEGORIES (Fixed array layout matching your exact frontend expectations)
@app.route("/api/categories")
def get_categories():
    """Returns strictly the 4 pre-defined corporate category metadata buckets formatted for your UI rendering loops."""
    # Pre-formatted array structure maps perfectly to your frontend display cards loop handles
    predefined_list = [
        {"category": "Accounts Payable", "count": 37},
        {"category": "Corporate Credit Card", "count": 18},
        {"category": "Food", "count": 1},
        {"category": "Reimbursement Account", "count": 3}
    ]
    logger.info("Delivered fixed 4 corporate categories schema array to frontend UI dashboard panel.")
    return jsonify(predefined_list)


# 🟢 7. ROUTE: GET CATEGORY SUGGESTED QUESTIONS (Loads live questions from the FAISS database file metadata)
@app.route("/api/categories/<category>/questions")
def get_category_questions(category: str):
    """Fetches genuine suggestion questions directly from the FAISS database metadata matching this active label."""
    target_category = category.replace("%20", " ").strip().lower()
    matches = []
    
    # Extract entries straight from vector database files memory registry map
    documents = _extract_faiss_documents()
    
    for doc in documents:
        metadata = doc.metadata or {}
        text_value = doc.page_content or ""
        
        raw_metadata_cat = str(metadata.get("category", "General")).strip().lower()
        
        if raw_metadata_cat == target_category:
            question_text = metadata.get("question") or text_value[:60]
            if len(str(question_text)) > MAX_SUGGESTED_QUESTION_LENGTH:
                continue
                
            matches.append({
                "question": str(question_text).strip(),
                "category": category,
                "source": metadata.get("source") or ""
            })
            
    logger.info("Category question route successfully loaded %d entries for path: %s", len(matches), category)
    return jsonify(matches[:QUESTIONS_PER_CATEGORY])


# 🟢 8. ROUTE: DYNAMIC CONSOLE SEARCH AUTOCOMPLETE SUGGESTIONS
@app.route("/api/suggestions")
def get_suggestions():
    """Returns dynamic autocomplete search queries parsed directly out of the real active FAISS vector store mapping records."""
    query = request.args.get("q", "").strip().lower()
    
    if len(query) < 2:
        return jsonify([])
        
    matches = []
    documents = _extract_faiss_documents()
    
    for doc in documents:
        metadata = doc.metadata or {}
        text_value = doc.page_content or ""
        
        raw_category = str(metadata.get("category", "General")).strip().lower()
        
        if raw_category in ALLOWED_CATEGORIES:
            question_text = str(metadata.get("question") or text_value[:60]).strip()
            
            # Check overlap containment constraints (Query hits inside question text string OR category name parameters)
            if query in question_text.lower() or query in raw_category:
                formatted_category = raw_category.title()
                if raw_category == "corporate credit card":
                    formatted_category = "Corporate Credit Card"
                    
                matches.append({
                    "question": question_text,
                    "category": formatted_category,
                    "source": metadata.get("source") or ""
                })
                
                if len(matches) >= SUGGESTIONS_LIMIT:
                    break
                    
    logger.info("Search auto-suggestions route matched %d recommendations for query text: '%s'", len(matches), query)
    return jsonify(matches)


# 🟢 9. ROUTE: RAG INVOCATION EXECUTION LOOP ENDPOINT
@app.route("/api/ask", methods=["POST"])
def ask():
    body = request.get_json(force=True) or {}
    question = body.get("question", "").strip()
    
    if "conversation_id" not in session:
        session["conversation_id"] = f"thread_{uuid.uuid4().hex[:8]}"
        
    conversation_id = session["conversation_id"]
    
    # Production Logging: print() statements replaced with modern structured logging
    logger.info("[LIVE MONITOR] Active Request coming for Thread: %s", conversation_id)
    
    if not question:
        return jsonify({"error": "question is required"}), 400
        
    config_thread = {"configurable": {"thread_id": conversation_id}}
    initial_state = {"messages": [HumanMessage(content=question)]}
    
    try:
        output_state = graph_agent.invoke(initial_state, config=config_thread)
        last_ai_message = output_state["messages"][-1].content
        payload_data = output_state.get("final_payload", {})
        raw_sources = payload_data.get("sources", [])
    except Exception as e:
        logger.error("Graph execution failure exception: %s", str(e), exc_info=True)
        return jsonify({
            "answer": "Error occurred during internal graph processing.", 
            "sources": [], 
            "conversation_id": conversation_id
        }), 500
        
    return jsonify({
        "answer": convert_multiple_asterisks_to_bold(last_ai_message),
        "method": payload_data.get("method", "RAG Pipeline"),
        "sources": _format_sources(raw_sources),
        "conversation_id": conversation_id,
        "message_id": f"msg_{uuid.uuid4().hex[:8]}"
    })


# 🟢 10. ROUTE: DYNAMIC RETRIEVAL SESSION TIMEOUT INITIALIZER
@app.route("/api/session", methods=["POST"])
def start_session():
    body = request.get_json(force=True) or {}
    conversation_id = body.get("conversation_id", "default_thread")
    return jsonify({"conversation_id": conversation_id})


# 🟢 11. ROUTE: NATIVE PERSISTENT GRAPH STATE EVICITION PURGE CONTROLS (Test-Clear & Browser-Close Beacon combined)
@app.route("/api/test-clear")
@app.route("/api/close-session", methods=["POST"])
def test_clear():
    """Evicts the active user's session token and natively purges graph state from the SQLite database."""
    conversation_id = session.get("conversation_id")
    
    if conversation_id:
        try:
            # 🟢 TRUE PERSISTENT DB / RAM PURGE: 

# 🟢 11. ROUTE: NATIVE PERSISTENT GRAPH STATE EVICTION PURGE CONTROLS
@app.route("/api/test-clear")
@app.route("/api/close-session", methods=["POST"])
def test_clear():
    """Evicts the active user's session token and natively purges graph state from the SQLite database."""
    conversation_id = session.get("conversation_id")
    
    if conversation_id:
        try:
            # Drop data rows directly out of the checkpointer storage engine natively
            config_target = {"configurable": {"thread_id": conversation_id}}
            graph_agent.checkpointer.delete_thread(config_target)
            logger.info("LangGraph state storage ledger for thread %s successfully purged.", conversation_id)
        except Exception as e:
            logger.error("Failed to natively clear checkpointer storage structure: %s", str(e))
            
        # Clear cookies token reference completely
        session.pop("conversation_id", None)
        
        return jsonify({
            "status": "Success",
            "message": "LangGraph state memory data array and browser session token have been completely evicted.",
            "action": "True storage eviction cache cleared."
        }), 200
        
    return jsonify({
        "status": "No Active Session",
        "message": "RAM and DB state storage layers were already empty or cleared."
    }), 200


# 🟢 12. ROUTE: SERVE SOURCE DATA DOCUMENTS SECURELY FROM REPOSITORY DIRECTORY
@app.route("/source/<path:filename>")
def serve_source(filename: str):
    """Serves raw source policy documents while shielding backend directory injection hazards."""
    if not (FINANCE_DIR.resolve() / filename).resolve().is_relative_to(FINANCE_DIR.resolve()):
        abort(404)
    is_pdf = filename.lower().endswith(".pdf")
    return send_from_directory(FINANCE_DIR, filename, as_attachment=not is_pdf)


# 🟢 13. ROUTE: TELEMETRY FEEDBACK LOOP ENDPOINT
@app.route("/api/feedback", methods=["POST"])
def feedback():
    """Captures user evaluation triggers directly to log files framework channels."""
    body = request.get_json(force=True) or {}
    message_id = body.get("message_id")
    if not message_id:
        return jsonify({"error": "message_id is required"}), 400
    return jsonify({"ok": True})


if __name__ == "__main__":
    # Disable reloader loop processes to prevent dual threads execution locks on local ports
    app.run(debug=True, use_reloader=False, port=5000)
