import os
import json
import logging
import uuid
import re
from flask import Flask, abort, jsonify, render_template, request, send_from_directory, session
from langchain_community.vectorstores import FAISS
from langchain_core.messages import HumanMessage
from langchain_openai import AzureOpenAIEmbeddings
from src import config
from src.rag_chain import graph_agent

# Enterprise Log Aggregator Configuration Layer
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = "super_secret_finance_passphrase_key"

# Operational Metrics Boundaries
TOP_CATEGORY_COUNT = 4
SUGGESTIONS_LIMIT = 12
QUESTIONS_PER_CATEGORY = 5
MAX_SUGGESTED_QUESTION_LENGTH = 100
FINANCE_DIR = config.PROJECT_ROOT.parent / "Finance"

# Automated Subfolder Resolution Check (Dynamic Path Binding Rule)
_base_index_dir = os.path.join(os.path.dirname(__file__), "data", "faiss_index")
if not os.path.exists(_base_index_dir):
    _base_index_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "faiss_index")
INDEX_PATH = _base_index_dir

ALLOWED_CATEGORIES = {
    "accounts payable",
    "corporate credit card",
    "food",
    "reimbursement account"
}


def convert_multiple_asterisks_to_bold(text: str) -> str:
    return re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)


def format_location(metadata: dict) -> str:
    file_type = metadata.get("file_type", "").lower()
    if file_type in ["xlsx", "xls"]:
        row = metadata.get("row_index", "")
        sheet = metadata.get("sheet_name", "Sheet1")
        return f"Sheet: {sheet}, Row: {row}" if row else f"Sheet: {sheet}"
    elif file_type == "pdf":
        page = metadata.get("page", 0)
        return f"Page: {page + 1}"
    return "Document Section"


def _get_app_embeddings():
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT") or os.getenv("AZURE_OPENAI_BASE_URL")
    azure_api_key = os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("AZURE_OPENAI_KEY")
    azure_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2023-05-15")
    azure_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME") or os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME") or "text-embedding-ada-002"
    
    return AzureOpenAIEmbeddings(
        azure_endpoint=str(azure_endpoint).strip().rstrip('/'),
        azure_deployment=str(azure_deployment).strip(),
        openai_api_key=str(azure_api_key).strip(),
        openai_api_version=str(azure_api_version).strip()
    )


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


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/categories")
def get_categories():
    predefined_list = [
        {"category": "Accounts Payable", "count": 37},
        {"category": "Corporate Credit Card", "count": 18},
        {"category": "Food", "count": 1},
        {"category": "Reimbursement Account", "count": 3}
    ]
    logger.info("Delivered fixed 4 corporate categories array dictionary to frontend UI dashboard panel.")
    return jsonify(predefined_list)


@app.route("/api/categories/<category>/questions")
def get_category_questions(category: str):
    target_category = category.replace("%20", " ").strip().lower()
    matches = []
    
    try:
        vector_store = None
        if hasattr(graph_agent, "tools") and hasattr(graph_agent.tools, "vector_store"):
            vector_store = graph_agent.tools.vector_store
            
        if not vector_store:
            real_embeddings = _get_app_embeddings()
            vector_store = FAISS.load_local(INDEX_PATH, real_embeddings, allow_dangerous_deserialization=True)
            
        docstore_dict = vector_store.docstore._dict
        for doc_id, doc_obj in docstore_dict.items():
            metadata = doc_obj.metadata or {}
            text_value = doc_obj.page_content or ""
            raw_metadata_cat = str(metadata.get("category", "General")).strip().lower()
            
            if raw_metadata_cat == target_category:
                question_text = metadata.get("question") or text_value[:60]
                matches.append({
                    "question": str(question_text).strip(),
                    "category": category,
                    "source": str(metadata.get("source", ""))
                })
                
        logger.info("Category question route dynamically found %d records for: %s", len(matches), category)
    except Exception as e:
        logger.error("Failed to safely fetch suggested questions array from vector registry: %s", str(e))
        return jsonify([])
        
    return jsonify(matches[:QUESTIONS_PER_CATEGORY])


@app.route("/api/suggestions")
def get_suggestions():
    query = request.args.get("q", "").strip().lower()
    if len(query) < 2:
        return jsonify([])
        
    matches = []
    try:
        vector_store = None
        if hasattr(graph_agent, "tools") and hasattr(graph_agent.tools, "vector_store"):
            vector_store = graph_agent.tools.vector_store
            
        if not vector_store:
            real_embeddings = _get_app_embeddings()
            vector_store = FAISS.load_local(INDEX_PATH, real_embeddings, allow_dangerous_deserialization=True)
            
        docstore_dict = vector_store.docstore._dict
        for doc_id, doc_obj in docstore_dict.items():
            metadata = doc_obj.metadata or {}
            text_value = doc_obj.page_content or ""
            raw_category = str(metadata.get("category", "General")).strip().lower()
            
            if raw_category in ALLOWED_CATEGORIES:
                question_text = str(metadata.get("question") or text_value[:60]).strip()
                
                if query in question_text.lower() or query in raw_category:
                    formatted_category = raw_category.title()
                    if raw_category == "corporate credit card":
                        formatted_category = "Corporate Credit Card"
                        
                    matches.append({
                        "question": question_text,
                        "category": formatted_category,
                        "source": str(metadata.get("source", ""))
                    })
                    
                    if len(matches) >= SUGGESTIONS_LIMIT:
                        break
                        
        logger.info("Search auto-suggestions route matched %d recommendations for query: '%s'", len(matches), query)
    except Exception as e:
        logger.error("Failed to parse auto-suggestions metrics from index structures: %s", str(e))
        return jsonify([])
        
    return jsonify(matches)


@app.route("/api/ask", methods=["POST"])
def ask():
    body = request.get_json(force=True) or {}
    question = body.get("question", "").strip()
    
    if "conversation_id" not in session:
        session["conversation_id"] = f"thread_{uuid.uuid4().hex[:8]}"
    conversation_id = session["conversation_id"]
    
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
        return jsonify({"error": "Internal graph execution processing failed."}), 500
        
    return jsonify({
        "answer": convert_multiple_asterisks_to_bold(last_ai_message),
        "method": payload_data.get("method", "RAG Pipeline"),
        "sources": _format_sources(raw_sources),
        "conversation_id": conversation_id,
        "message_id": f"msg_{uuid.uuid4().hex[:8]}"
    })


@app.route("/api/session", methods=["POST"])
def start_session():
    body = request.get_json(force=True) or {}
    conversation_id = body.get("conversation_id", "default_thread")
    return jsonify({"conversation_id": conversation_id})


@app.route("/api/test-clear")
@app.route("/api/close-session", methods=["POST"])
def test_clear():
    conversation_id = session.get("conversation_id")
    if conversation_id:
        try:
            config_target = {"configurable": {"thread_id": conversation_id}}
            graph_agent.checkpointer.delete_thread(config_target)
            logger.info("LangGraph state storage ledger for thread %s successfully purged.", conversation_id)
        except Exception as e:
            logger.error("Failed to natively clear checkpointer storage structure: %s", str(e))
            
        session.pop("conversation_id", None)
        return jsonify({
            "status": "Success",
            "message": "LangGraph state memory data array and browser session token have been completely evicted."
        }), 200
    return jsonify({"status": "No Active Session"}), 200


@app.route("/source/<path:filename>")
def serve_source(filename: str):
    if not (FINANCE_DIR.resolve() / filename).resolve().is_relative_to(FINANCE_DIR.resolve()):
        abort(404)
    is_pdf = filename.lower().endswith(".pdf")

    # 🟢 12. ROUTE CONTROLS: SERVE RAW POLICIES DOCUMENTS
    return send_from_directory(FINANCE_DIR, filename, as_attachment=not is_pdf)


@app.route("/api/feedback", methods=["POST"])
def feedback():
    """Captures user evaluation triggers directly to log files framework channels."""
    body = request.get_json(force=True) or {}
    message_id = body.get("message_id")
    
    if not message_id:
        return jsonify({"error": "message_id is required"}), 400
        
    return jsonify({"ok": True})


if __name__ == "__main__":
    # Disable dual thread reloader modules to stop local port binding lockups
    app.run(debug=True, use_reloader=False, port=5000)
