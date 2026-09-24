@tool
def retrieve_knowledge_base(query: str) -> str:
    """Search across the company financial warehouse (Excel FAQs, Word docs, and PDFs)."""
    hits = retrieve(query)
    
    # Validation check: Agar hits khali hain toh empty return karein
    if not hits or not isinstance(hits, list) or len(hits) == 0:
        return json.dumps([])
        
    # 🟢 FIXED DATA EXTRACTION: Grab the absolute top hit at index 0 from the list
    top_hit = hits[0] 
    metadata = top_hit.get("metadata", {})
    
    is_xlsx = metadata.get("file_type") == "xlsx" or str(metadata.get("source", "")).lower().endswith(('.xlsx', '.xls'))
    mapped_answer = metadata.get("answer")
    
    # Dynamic binding matching your screenshot config.py parameters cleanly
    target_threshold = getattr(config, "DIRECT_ANSWER_MIN_SCORE", 0.6)
    
    # Test conditions securely now
    if is_xlsx and mapped_answer and float(top_hit.get("score", 0.0)) >= target_threshold:
        # Pura list pass karein json structures me takki app.py use index kar sake
        return f"[EXCEL_FAQ_DIRECT_HIT] {json.dumps(top_hit)}"
        
    return json.dumps(hits)
