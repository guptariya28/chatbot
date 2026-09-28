# 📍 FILE: app.py | Replace your category questions and suggestions routes with these versions

# Re-use the successfully compiled graph engine properties directly
from src.rag_chain import graph_agent

@app.route("/api/categories/<category>/questions")
def get_category_questions(category: str):
    """Fetches genuine suggestion questions directly from the pre-loaded FAISS Vector DB instance."""
    target_category = category.replace("%20", " ").strip().lower()
    matches = []
    
    try:
        # 🟢 THE INSTANT PRO CORNER-CUT HOOK:
        # Re-use the active compiled vector store from your pipeline graph setup.
        # This bypasses all manual file-loading loops and dimension crashes!
        vector_store = None
        if hasattr(graph_agent, "tools") and hasattr(graph_agent.tools, "vector_store"):
            vector_store = graph_agent.tools.vector_store
            
        # Fallback if your custom graph class structure organizes it differently:
        if not vector_store:
            from src.retrieval.retriever import _get_active_embeddings
            embeddings = _get_active_embeddings()
            vector_store = FAISS.load_local(INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
            
        # Access internal database document store mapping directly in memory
        docstore_dict = vector_store.docstore._dict
        
        for doc_id, doc_obj in docstore_dict.items():
            metadata = doc_obj.metadata or {}
            text_value = doc_obj.page_content or ""
            
            raw_metadata_cat = str(metadata.get("category", "General")).strip().lower()
            
            # Direct target verification string check
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
        
    # Return top 3 questions according to standard template constraints
    return jsonify(matches[:QUESTIONS_PER_CATEGORY])


@app.route("/api/suggestions")
def get_suggestions():
    """Returns dynamic autocomplete search queries parsed out of the active vector database."""
    query = request.args.get("q", "").strip().lower()
    
    if len(query) < 2:
        return jsonify([])
        
    matches = []
    
    try:
        vector_store = None
        if hasattr(graph_agent, "tools") and hasattr(graph_agent.tools, "vector_store"):
            vector_store = graph_agent.tools.vector_store
            
        if not vector_store:
            from src.retrieval.retriever import _get_active_embeddings
            embeddings = _get_active_embeddings()
            vector_store = FAISS.load_local(INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
            
        docstore_dict = vector_store.docstore._dict
        
        for doc_id, doc_obj in docstore_dict.items():
            metadata = doc_obj.metadata or {}
            text_value = doc_obj.page_content or ""
            
            raw_category = str(metadata.get("category", "General")).strip().lower()
            
            if raw_category in ALLOWED_CATEGORIES:
                question_text = str(metadata.get("question") or text_value[:60]).strip()
                
                # Check overlap containment (Query matches inside question string OR category)
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
