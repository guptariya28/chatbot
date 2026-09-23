"""
Flask web app for the finance chatbot: serves the chat UI and exposes
a small JSON API that wraps a LangGraph multi-user conversational state machine.
"""

import json
import logging
import os
import re
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

# --- Load metadata items for search autocomplete/suggestions ---
TOP_CATEGORY_COUNT = 6
SUGGESTIONS_LIMIT = 12
QUESTIONS_PER_CATEGORY = 3
MAX_SUGGESTIONS_QUESTION_LENGTH = 100

def _load_faq_index() -> list[dict]:
    if not config.RAW_DOCUMENTS_PATH.exists():
        logger.warning("raw_documents.jsonl not found - run the ingestion pipeline first.")
        return []
    entries = []
    with config.RAW_DOCUMENTS_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            doc = json.loads(line)
            metadata = doc["metadata"]
            question = metadata.get("question")
            if not question or len(question) > MAX_SUGGESTIONS_QUESTION_LENGTH:
                continue
            entries.append({
                "question": question,
                "category": metadata.get("category") or "General",
                "source": metadata.get("source"),
            })
    return entries

FAQ_INDEX = _load_faq_index()

# --------------------------------------------------------------------------
# Azure OpenAI Integration mapping your generator.py configs Natively
# --------------------------------------------------------------------------
llm = AzureChatOpenAI(
    azure_deployment=config.AZURE_OPENAI_CHAT_DEPLOYMENT,
    api_version="2024-05-01-preview",
    temperature=getattr(config, "GENERATION_TEMPERATURE", 0),
    max_tokens=getattr(config, "GENERATION_MAX_TOKENS", None)
)

TOOLS = [retrieve_knowledge_base]
TOOLS_BY_NAME = {t.name: t for t in TOOLS}
llm_with_tools = llm.bind_tools(TOOLS)

# Safety citation clean-up regex compile straight from your generator.py
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
    formatted_messages = []
    
    # Re-structure context formatting precisely how generator.py handled it
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
    
    # Apply your generator.py citation stripping safety filter natively
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
        
        # Intercept if the tool flagged a Direct FAQ hit to bypass the LLM completely
        if raw_result.startswith("[EXCEL_FAQ_DIRECT_HIT]"):
            faq_match = True
            raw_result = raw_result.replace("[EXCEL_FAQ_DIRECT_HIT] ", "")
            hits = json.loads(raw_result)
            
            # Extract the direct text from your raw Excel row
            direct_ans = hits[0]["metadata"]["answer"]
            
            tool_messages.append(ToolMessage(content=direct_ans, tool_call_id=call["id"], name=call["name"]))
            payload_response = {"answer": direct_ans, "method": "Direct FAQ Row Match (LLM Saved)", "sources": hits}
            debug_contexts.append(f"[EXCEL DIRECT FAQ HIT]: {direct_ans}")
            break
        
        # Standard Document Processing Flow (PDF / Docx / standard table blocks)
        hits = json.loads(raw_result)
        tool_messages.append(ToolMessage(content=raw_result, tool_call_id=call["id"], name=call["name"]))
        debug_contexts.append(raw_result)
        payload_response = {"sources": hits, "method": "RAG Pipeline (Azure OpenAI Synth)"}

    # CRUCIAL REQUIREMENT: OVERWRITE DEBUGGER.TXT ON EVERY QUESTION WITH ENTIRE RETRIEVED BLOCKS
    with open("debugger.txt", "w", encoding="utf-8") as f:
        f.write("=== LAST RETRIEVED CONTEXT POOL ===\n")
        f.write("\n\n".join(debug_contexts))

    return {"messages": tool_messages, "is_direct_faq": faq_match, "final_payload": payload_response}

def direct_answer_node(state: AgentState) -> dict:
    """Instantly delivers the spreadsheet response without hitting Azure OpenAI."""
    payload = state.get("final_payload", {})
    return {"messages": [AIMessage(content=payload.get("answer", ""))]}

# --- Graph Route Conditions ---
def route_after_agent(state: AgentState) -> str:
    last_msg = state["messages"][-1]
    if isinstance(last_msg, AIMessage) and last_msg.tool_calls:
        return "retrieve"
    return END

def route_after_retrieve(state: AgentState) -> str:
    if state.get("is_direct_faq", False):
        return "direct_answer"
    return "agent"

# Compile State Machine with full in-memory chat session thread support
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
        if entry["category"] == "General":
            continue
        counts[entry["category"]] = counts.get(entry["category"], 0) + 1
    top = sorted(counts.items(), key=lambda kv: kv, reverse=True)[:TOP_CATEGORY_COUNT]
    return jsonify([{"category": name, "count": count} for name, count in top])

@app.route("/api/categories/<category>/questions")
def get_category_questions(category: str):
    matches = [e["question"] for e in FAQ_INDEX if e["category"] == category]
    return jsonify(matches[:QUESTIONS_PER_CATEGORY])

@app.route("/api/suggestions")
def get_suggestions():
    query = request.args.get("q", "").strip().lower()
    if len(query) < 2:
        return jsonify([])
