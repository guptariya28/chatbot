"""
Flask web app for the finance chatbot: serves the chat UI and exposes
a small JSON API that wraps a LangGraph multi-user conversational state machine.
"""

import json
import logging
import os
import re
import uuid
from typing import Annotated, Sequence, TypedDict
from flask import Flask, abort, jsonify, render_template, request, send_from_directory

# Configurations & Source Mapping Helpers
from src import config
from src.rag_chain import format_location
from src.retrieval.retriever import retrieve_knowledge_base

# LangGraph & LangChain components for Azure OpenAI
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

FINANCE_DIR = config.PROJECT_ROOT.parent / "Finance"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)

# --- FAQ index config for UI categories chips + search autocomplete ---
TOP_CATEGORY_COUNT = 6
SUGGESTIONS_LIMIT = 12
QUESTIONS_PER_CATEGORY = 3
MAX_SUGGESTED_QUESTION_LENGTH = 100

def _load_faq_index() -> list[dict]:
    """Load xlsx-derived entries for the UI without strict parameter drops."""
    if not config.RAW_DOCUMENTS_PATH.exists():
        logger.warning("raw_documents.jsonl not found - run the ingestion pipeline first.")
        return []
    entries = []
    with config.RAW_DOCUMENTS_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            doc = json.loads(line)
            metadata = doc.get("metadata", {})
            question = metadata.get("question")
            # If explicit question field is missing, fallback to snippet text mapping safely
            if not question:
                question = doc.get("text", "")[:60]
            if len(question) > MAX_SUGGESTED_QUESTION_LENGTH:
                continue
            entries.append({
                "question": question,
                "category": metadata.get("category") or "General",
                "source": metadata.get("source", ""),
            })
    return entries

FAQ_INDEX = _load_faq_index()

# --------------------------------------------------------------------------
# Azure OpenAI Integration mapping your configs safely inside brackets
# --------------------------------------------------------------------------
llm = AzureChatOpenAI(
    azure_deployment=config.AZURE_OPENAI_CHAT_DEPLOYMENT,
    api_version="2024-05-01-preview",
    temperature=getattr(config, "GENERATION_TEMPERATURE", 0),
    max_tokens=getattr(config, "GENERATION_MAX_TOKENS", None),
    api_key=getattr(config, "AZURE_OPENAI_KEY", os.getenv("AZURE_OPENAI_KEY")),
    azure_endpoint=getattr(config, "AZURE_OPENAI_ENDPOINT", os.getenv("AZURE_OPENAI_ENDPOINT"))
)

TOOLS = [retrieve_knowledge_base]
llm_with_tools = llm.bind_tools(TOOLS)

TOOLS_BY_NAME = {t.name: t for t in TOOLS}
SOURCE_CITATION_PATTERN = re.compile(r"\s*\(Source:[^)]*\)", re.IGNORECASE)

# --------------------------------------------------------------------------
# LangGraph Workflow Architecture Design
# --------------------------------------------------------------------------
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    is_direct_faq: bool
    final_payload: dict 

def agent_node(state: AgentState) -> dict:
    """Executes the LLM with your strict generator.py SYSTEM_PROMPT rules."""
    SYSTEM_PROMPT = (
        "You are a finance helpdesk assistant. Answer the user's question "
        "using ONLY the context provided below. If the context does not "
        "contain enough information to answer, say so clearly instead of "
        "guessing. Keep answers concise and answer directly - do not start "
        "with a greeting like 'Hello' or 'Hi'. Do not cite or mention source "
        "file names in your answer text; sources are shown separately in the "
        "UI, so never write things like '(Source: ...)'."
    )
    
    messages = list(state["messages"])
    
    # 100% BULLETPROOF SEQUENCE TRIMMER:
    # Instead of raw slicing which leaves orphaned ToolMessages, we slice by complete user turns (pairs).
    # This keeps the last 2 complete back-and-forth interactions safely.
    if len(messages) > 4:
        # Loop backwards to find the last HumanMessage and keep the context sequence valid
        trimmed_messages = []
        human_count = 0
        for msg in reversed(messages):
            trimmed_messages.insert(0, msg)
            if isinstance(msg, HumanMessage):
                human_count += 1
                if human_count >= 2:  # Keep last 2 user turns with all their inner tool responses
                    break
        messages = trimmed_messages

    formatted_messages = []
    for msg in messages:
        if msg.type == "system":
            continue
        if isinstance(msg, ToolMessage):
            try:
                raw_hits = json.loads(msg.content)
                blocks = []
                for i, chunk in enumerate(raw_hits):
                    src_name = chunk.get('metadata', {}).get('source', 'unknown')
                    blocks.append(f"[{i + 1}] (Source: {src_name})\n{chunk.get('text', '')}")
                context_string = "\n\n".join(blocks)
                
                formatted_messages.append(ToolMessage(
                    content=f"Context:\n{context_string}\n\nAnswer using only the context above.",
                    tool_call_id=msg.tool_call_id,
                    name=msg.name
                ))
            except Exception:
                formatted_messages.append(msg)
        else:
            formatted_messages.append(msg)
            
    final_input_stream = [HumanMessage(content=SYSTEM_PROMPT)] + formatted_messages
    response = llm_with_tools.invoke(final_input_stream)
    
    if response.content:
        response.content = SOURCE_CITATION_PATTERN.sub("", response.content).strip()
        
    return {"messages": [response]}

def retrieve_node(state: AgentState) -> dict:
    """Triggers the retriever tool, creates debugger logs, and checks for FAQ short-circuit."""
    last_msg = state["messages"][-1]
    tool_messages = []
    faq_match = False
    debug_contexts = []
    payload_response = {}

    for call in last_msg.tool_calls:
        tool_fn = TOOLS_BY_NAME[call["name"]]
        raw_result = tool_fn.invoke(call["args"])
        
        if raw_result.startswith("[EXCEL_FAQ_DIRECT_HIT]"):
            faq_match = True
            raw_result = raw_result.replace("[EXCEL_FAQ_DIRECT_HIT] ", "")
            hits = json.loads(raw_result)
            direct_ans = hits[0]["metadata"]["answer"]
            
            tool_messages.append(ToolMessage(content=direct_ans, tool_call_id=call["id"], name=call["name"]))
            payload_response = {"answer": direct_ans, "method": "Direct FAQ Row Match (LLM Saved)", "sources": hits}
            debug_contexts.append(f"[EXCEL DIRECT FAQ HIT]: {direct_ans}")
            break
        
        hits = json.loads(raw_result)
        tool_messages.append(ToolMessage(content=raw_result, tool_call_id=call["id"], name=call["name"]))
        debug_contexts.append(raw_result)
        payload_response = {"sources": hits, "method": "RAG Pipeline (Azure OpenAI Synth)"}

    # OVERWRITE DEBUGGER.TXT LIVE SESSIONS ON EVERY QUESTION
    with open("debugger.txt", "w", encoding="utf-8") as f:
        f.write("=== LAST RETRIEVED CONTEXT POOL ===\n")
        f.write("\n\n".join(debug_contexts))

    return {"messages": tool_messages, "is_direct_faq": faq_match, "final_payload": payload_response}

def direct_answer_node(state: AgentState) -> dict:
    payload = state.get("final_payload", {})
    return {"messages": [AIMessage(content=payload.get("answer", ""))]}

def route_after_agent(state: AgentState) -> str:
    last_msg = state["messages"][-1]
    if isinstance(last_msg, AIMessage) and last_msg.tool_calls:
        return "retrieve"
    return END

def route_after_retrieve(state: AgentState) -> str:
    if state.get("is_direct_faq", False):
        return "direct_answer"
    return "agent"

# Build execution tree graph properties safely
workflow = StateGraph(AgentState)
workflow.add_node("agent", agent_node)
workflow.add_node("retrieve", retrieve_node)
workflow.add_node("direct_answer", direct_answer_node)

workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", route_after_agent, {"retrieve": "retrieve", END: END})
workflow.add_conditional_edges("retrieve", route_after_retrieve, {"direct_answer": "direct_answer", "agent": "agent"})
workflow.add_edge("direct_answer", END)

graph_agent = workflow.compile(checkpointer=MemorySaver())

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
# Flask Endpoints Integration
# --------------------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/categories")
def get_categories():
    counts: dict[str, int] = {}
    for entry in FAQ_INDEX:
        cat_name = str(entry.get("category", "General")).strip()
        if not cat_name or cat_name.lower() == "general":
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
    # use_reloader=False blocks any dynamic execution crashes permanently!
    app.run(debug=True, use_reloader=False, port=5000)
