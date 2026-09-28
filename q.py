def _get_cached_vector_store(embeddings) -> bool:
    """Maintains a single persistent RAM registry cache copy of the FAISS index database."""
    global _cached_vector_store
    if _cached_vector_store is None:
        logger.info("Initializing cold-boot load of FAISS indices binary workspace from disk...")
        _cached_vector_store = load_faiss_store_natively(embeddings)
        if _cached_vector_store:
            logger.info("🎉 SUCCESS! FAISS vector cluster successfully pinned inside server RAM.")
        else:
            logger.error("❌ CRITICAL: Failed to load vector database structure into active memory.")
            return False
    return True


def retrieve(query: str, top_k: int = config.FINAL_TOP_K) -> list[dict]:
    """🟢 ENTERPRISE RETRIEVAL ENGINE:

    Executes near-instant vector similarity matches directly out of cached server RAM allocations.
    """
    if not query.strip():
        return []
        
    try:
        embeddings = _get_active_embeddings()
        if not _get_cached_vector_store(embeddings):
            return []
            
        logger.info("Executing dense vector scan operations loop for query text: %r", query)
        raw_results = _cached_vector_store.similarity_search_with_score(query, k=top_k)
        
        formatted_chunks = []
        for doc, score in raw_results:
            # LangChain FAISS L2 metric score mapping transformation back to standard 0.0 - 1.0 ranges
            cosine_sim = 1.0 - (float(score) / 2.0) if float(score) <= 2.0 else 0.0
            
            formatted_chunks.append({
                "text": doc.page_content,
                "metadata": doc.metadata or {},
                "score": cosine_sim
            })
            
        return formatted_chunks
        
    except Exception as e:
        logger.error("Failed to query vector database elements from cached retriever: %s", str(e), exc_info=True)
        return []


@tool
def retrieve_knowledge_base(query: str) -> str:
    """Search across the company financial warehouse (Excel FAQs, Word docs, and PDFs)."""
    hits = retrieve(query)
    
    if not hits or not isinstance(hits, list) or len(hits) == 0:
        return json.dumps([])
        
    # Safely extract index element 0 to evaluate short-circuit direct matches parameters
    top_hit = hits[0]
    metadata = top_hit.get("metadata", {})
    
    is_xlsx = metadata.get("file_type") == "xlsx" or str(metadata.get("source", "")).lower().endswith(('.xlsx', '.xls'))
    mapped_answer = metadata.get("answer")
    target_threshold = getattr(config, "DIRECT_ANSWER_MIN_SCORE", 0.7)
    
    if is_xlsx and mapped_answer and float(top_hit.get("score", 0.0)) >= target_threshold:
        logger.info("🎯 FAQ SHORT-CIRCUIT TRIGGERED: Top Hit Vector Score: %f", float(top_hit.get("score", 0.0)))
        return f"[EXCEL_FAQ_DIRECT_HIT] {json.dumps(hits)}"
        
    return json.dumps(hits)



# 📍 FILE: src/rag_chain.py | Replace your retrieve_node function completely

def retrieve_node(state: AgentState) -> dict:
    """🟢 PRODUCTION RETRIEVAL NODE:
    Natively packages context arrays to pass seamlessly to the LangGraph execution model.
    Guarantees that index element 0 is unwrapped safely without index type errors.
    """
    messages = state.get("messages", [])
    if not messages:
        return {"messages": [], "final_payload": {"sources": [], "method": "RAG Fallback"}}
        
    last_user_query = messages[-1].content
    logger.info("Executing retrieval graph node search for query: %r", last_user_query)
    
    # 1. Fetch raw matching vector chunk arrays from the optimized retriever module
    hits = retrieve(last_user_query)
    
    # Safe guard constraint checks to handle absolute empty vector spaces cleanly
    if not hits or not isinstance(hits, list) or len(hits) == 0:
        logger.warning("FAISS vector search database returned 0 matching records contexts.")
        return {
            "messages": [ToolMessage(
                content=json.dumps([]),
                tool_call_id=f"call_{uuid.uuid4().hex[:8]}",
                name="retrieve_knowledge_base"
            )],
            "final_payload": {"sources": [], "method": "Sparse Scan Fallback"}
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
        logger.info("🎯 EXCEL FAQ SHORT-CIRCUIT TRIGGERED: Direct hit verified at score %f", current_score)
        return {
            "messages": [AIMessage(content=f"[EXCEL_FAQ_DIRECT_HIT] {json.dumps(hits)}")],
            "final_payload": {"sources": hits, "method": "Excel FAQ Short-Circuit Bypass"}
        }
        
    # 3. Standard contextual validation wrapper loop for deep AI generation chains
    tool_message_artifact = ToolMessage(
        content=json.dumps(hits),
        tool_call_id=f"call_{uuid.uuid4().hex[:8]}",
        name="retrieve_knowledge_base"
    )
    
    return {
        "messages": [tool_message_artifact],
        "final_payload": {"sources": hits, "method": "Standard RAG Neural Processing"}
    }
