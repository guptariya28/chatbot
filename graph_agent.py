"""LangGraph Multi-User RAG State Graph Orchestration Machine Engine."""

import os
import json
import re
from typing import Annotated, Sequence, TypedDict

from src import config
from src.retrieval.retriever import retrieve_knowledge_base

# LangGraph & LangChain components for Azure OpenAI
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

# Initialize Azure OpenAI Model natively using your config fields safely
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
    
    raw_messages = list(state["messages"])
    
    # 🟢 DYNAMIC CRASH-PROOF SLIDING WINDOW:
    WINDOW_SIZE = 6 
    if len(raw_messages) > WINDOW_SIZE:
        candidate_messages = raw_messages[-WINDOW_SIZE:]
        while candidate_messages and (
            isinstance(candidate_messages, ToolMessage) or 
            (isinstance(candidate_messages, AIMessage) and candidate_messages.tool_calls)
        ):
            candidate_messages = candidate_messages[1:]
        messages = candidate_messages
    else:
        messages = raw_messages

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
            direct_ans = hits["metadata"]["answer"]
            
            tool_messages.append(ToolMessage(content=direct_ans, tool_call_id=call["id"], name=call["name"]))
            payload_response = {"answer": direct_ans, "method": "Direct FAQ Row Match (LLM Saved)", "sources": [hits]}
            debug_contexts.append(f"[EXCEL DIRECT FAQ HIT]: {direct_ans}")
            break
        
        hits = json.loads(raw_result)
        tool_messages.append(ToolMessage(content=raw_result, tool_call_id=call["id"], name=call["name"]))
        debug_contexts.append(raw_result)
        payload_response = {"sources": hits, "method": "RAG Pipeline (Azure OpenAI Synth)"}

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

# Assemble Flowchart Workflow properties cleanly
workflow = StateGraph(AgentState)
workflow.add_node("agent", agent_node)
workflow.add_node("retrieve", retrieve_node)
workflow.add_node("direct_answer", direct_answer_node)

workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", route_after_agent, {"retrieve": "retrieve", END: END})
workflow.add_conditional_edges("retrieve", route_after_retrieve, {"direct_answer": "direct_answer", "agent": "agent"})
workflow.add_edge("direct_answer", END)

# Export compiled runnable graph instance variable cleanly
graph_agent = workflow.compile(checkpointer=MemorySaver())
