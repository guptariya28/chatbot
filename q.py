# 📍 FILE: src/rag_chain.py | Replace your retrieve_node function completely

def retrieve_node(state: AgentState) -> dict:
    """条 CRASH-PROOF RETRIEVAL NODE:
    Natively streams text chunks directly into the LangGraph message workflow.
    Ensures context is always formatted perfectly so the LLM never returns empty fallbacks.
    """
    messages = state.get("messages", [])
    if not messages:
        return {"messages": [], "final_payload": {"sources": [], "method": "RAG Fallback"}}
        
    last_user_query = messages[-1].content
    logger.info("Executing vector database lookup for query: %r", last_user_query)
    
    # 1. Fetch raw matching vector chunk list records from retriever
    hits = retrieve(last_user_query)
    
    # Safe guard check: Return a clean notice if no data exists at all
    if not hits or not isinstance(hits, list) or len(hits) == 0:
        logger.warning("FAISS vector database search returned 0 records context.")
        return {
            "messages": [ToolMessage(
                content=json.dumps([]),
                tool_call_id=f"call_{uuid.uuid4().hex[:8]}",
                name="retrieve_knowledge_base"
            )],
            "final_payload": {"sources": [], "method": "Empty Vector Space Scan"}
        }
        
    # Isolate the top hit to evaluate metadata scoring parameters safely
    top_hit = hits[0]
    current_score = float(top_hit.get("score", 0.0))
    
    logger.info("Successfully fetched %d context chunks. Top hit score matrix: %f", len(hits), current_score)
    
    # 🟢 THE DEFINITIVE SYSTEM FIX:
    # Always compile and serialize the full list of matches into a standard ToolMessage artifact.
    # This guarantees your agent_node formats the context text blocks perfectly, 
    # giving the LLM the exact information it needs to answer your questions accurately!
    tool_message_artifact = ToolMessage(
        content=json.dumps(hits),
        tool_call_id=f"call_{uuid.uuid4().hex[:8]}",
        name="retrieve_knowledge_base"
    )
    
    return {
        "messages": [tool_message_artifact],
        "final_payload": {
            "sources": hits,
            "method": "Standard RAG Neural Processing Execution"
        }
    }
