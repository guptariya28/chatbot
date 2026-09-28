# 📍 FILE: src/rag_chain.py | Replace your retrieve_node function completely

def retrieve_node(state: AgentState) -> dict:
    """🟢 CRASH-PROOF RETRIEVAL NODE:
    Safely targets element index 0 to unwrap list dictionaries arrays cleanly.
    """
    messages = state.get("messages", [])
    if not messages:
        return {"messages": [], "final_payload": {"sources": [], "method": "Fallback"}}
        
    last_user_query = messages[-1].content
    logger.info("Executing retrieval search loop configuration for text: %r", last_user_query)
    
    # 1. Fetch raw matching vector chunk list dictionaries arrays from retriever
    hits = retrieve(last_user_query)
    
    if not hits or not isinstance(hits, list) or len(hits) == 0:
        return {
            "messages": [AIMessage(content="I could not find any relevant documentation.")],
            "final_payload": {"sources": [], "method": "Sparse Scan"}
        }
        
    # 🟢 THE SYSTEM CORNER-CUT POINTER HOOK:
    # Safely targets index element 0 to extract the top-ranked vector hit block dictionary!
    top_hit = hits[0]
    metadata = top_hit.get("metadata", {})
    
    is_xlsx = metadata.get("file_type") == "xlsx" or str(metadata.get("source", "")).lower().endswith(('.xlsx', '.xls'))
    mapped_answer = metadata.get("answer")
    target_threshold = getattr(config, "DIRECT_ANSWER_MIN_SCORE", 0.7)
    current_score = float(top_hit.get("score", 0.0))
    
    # 2. Evaluate fast-track business short-circuit logic configurations
    if is_xlsx and mapped_answer and current_score >= target_threshold:
        logger.info("🎯 FAQ SHORT-CIRCUIT TRIGGERED: Direct hit verified at score %f", current_score)
        return {
            "messages": [AIMessage(content=f"[EXCEL_FAQ_DIRECT_HIT] {json.dumps(hits)}")],
            "final_payload": {"sources": hits, "method": "Excel FAQ Short-Circuit"}
        }
        
    # 3. Standard contextual validation wrapper loop for tool artifact processing
    tool_message_artifact = ToolMessage(
        content=json.dumps(hits),
        tool_call_id=f"call_{uuid.uuid4().hex[:8]}",
        name="retrieve_knowledge_base"
    )
    
    return {
        "messages": [tool_message_artifact],
        "final_payload": {"sources": hits, "method": "Standard RAG Neural Processing"}
    }
# 📍 FILE: src/retrieval/retriever.py | Replace your retrieve_knowledge_base tool completely

@tool
def retrieve_knowledge_base(query: str) -> str:
    """Search across the company financial warehouse (Excel FAQs, Word docs, and PDFs)."""
    # 1. Fetch raw matching vector chunk list dictionaries arrays from retriever
    hits = retrieve(query)
    
    if not hits or not isinstance(hits, list) or len(hits) == 0:
        return json.dumps([])
        
    # 🟢 THE SYSTEM CORNER-CUT POINTER HOOK:
    # Access index element 0 safely here as well to isolate the top-ranked record match!
    top_hit = hits[0]
    metadata = top_hit.get("metadata", {})
    
    is_xlsx = metadata.get("file_type") == "xlsx" or str(metadata.get("source", "")).lower().endswith(('.xlsx', '.xls'))
    mapped_answer = metadata.get("answer")
    target_threshold = getattr(config, "DIRECT_ANSWER_MIN_SCORE", 0.7)
    
    if is_xlsx and mapped_answer and float(top_hit.get("score", 0.0)) >= target_threshold:
        logger.info("🎯 FAQ SHORT-CIRCUIT TRIGGERED: Top Hit Vector Score: %f", float(top_hit.get("score", 0.0)))
        return f"[EXCEL_FAQ_DIRECT_HIT] {json.dumps(hits)}"
        
    return json.dumps(hits)
