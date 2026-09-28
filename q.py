# 📍 FILE: src/rag_chain.py | Replace your retrieve_node function completely

def retrieve_node(state: AgentState) -> dict:
    """🟢 CRASH-PROOF RETRIEVAL NODE:
    Safely targets element index 0 to unwrap list dictionaries arrays cleanly.
    This completely eliminates 'TypeError: List indices must be integers or slices, not str'
    """
    messages = state.get("messages", [])
    if not messages:
        return {"messages": [], "final_payload": {"sources": [], "method": "Fallback"}}
        
    last_user_query = messages[-1].content
    logger.info("Executing retrieval search loop configuration for text: %r", last_user_query)
    
    # 1. Fetch raw matching vector chunk list dictionaries arrays from retriever
    hits = retrieve(last_user_query)
    
    # Secure validation check safeguards: Prevent runtime crashes on empty arrays
    if not hits or not isinstance(hits, list) or len(hits) == 0:
        logger.warning("Vector database lookup search returned 0 matching records contexts.")
        return {
            "messages": [AIMessage(content="I could not find any relevant documentation to answer your question.")],
            "final_payload": {"sources": [], "method": "Sparse Scan"}
        }
        
    # 🟢 THE DEFINITIVE PRODUCTION FIX:
    # Safely target index element 0 to extract the top-ranked vector hit block dictionary!
    # This completely overrides the old crashing lines like hits["metadata"]["answer"]
    top_hit = hits[0]
    metadata = top_hit.get("metadata", {})
    
    is_xlsx = metadata.get("file_type") == "xlsx" or str(metadata.get("source", "")).lower().endswith(('.xlsx', '.xls'))
    mapped_answer = metadata.get("answer")
    
    target_threshold = getattr(config, "DIRECT_ANSWER_MIN_SCORE", 0.7)
    current_score = float(top_hit.get("score", 0.0))
    
    # 2. Evaluate fast-track business short-circuit logic configurations conditions securely
    if is_xlsx and mapped_answer and current_score >= target_threshold:
        logger.info("🎯 EXCEL FAQ SHORT-CIRCUIT TRIGGERED: Direct hit verified at score %f", current_score)
        
        direct_response_string = f"[EXCEL_FAQ_DIRECT_HIT] {json.dumps(hits)}"
        
        return {
            "messages": [AIMessage(content=direct_response_string)],
            "final_payload": {
                "sources": hits,
                "method": "Excel FAQ Short-Circuit Bypass"
            }
        }
        
    # 3. Standard contextual validation wrapper loop for deep AI generation chains
    logger.info("Executing standard fallback processing loops channel. Top hit score: %f", current_score)
    
    tool_message_artifact = ToolMessage(
        content=json.dumps(hits),
        tool_call_id=f"call_{uuid.uuid4().hex[:8]}",
        name="retrieve_knowledge_base"
    )
    
    return {
        "messages": [tool_message_artifact],
        "final_payload": {
            "sources": hits,
            "method": "Standard RAG Neural Processing"
        }
    }
