# 📍 FILE: app.py | Replace your category questions and suggestions routes with these versions

from langchain_openai import AzureOpenAIEmbeddings

def _get_app_embeddings():
    """Natively reads credentials from the environment for suggestions and categories routes."""
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


@app.route("/api/categories/<category>/questions")
def get_category_questions(category: str):
    """Fetches genuine suggestion questions directly from the FAISS database metadata matching this active label."""
    target_category = category.replace("%20", " ").strip().lower()
    matches = []
    
    try:
        if not os.path.exists(INDEX_PATH):
            return jsonify([])
            
        # Real embeddings pass karein taaki dimensional AssertionError na aaye
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
                
        logger.info("Category question route successfully loaded %d entries for path: %s", len(matches), category)
    except Exception as e:
        logger.error("Failed to dynamically read category questions from FAISS: %s", str(e))
        return jsonify([])
        
    return jsonify(matches[:QUESTIONS_PER_CATEGORY])


@app.route("/api/suggestions")
def get_suggestions():
    """Returns dynamic autocomplete search queries parsed directly out of the real active FAISS vector store mapping records."""
    query = request.args.get("q", "").strip().lower()
    
    if len(query) < 2:
        return jsonify([])
        
    matches = []
    
    try:
        if not os.path.exists(INDEX_PATH):
            return jsonify([])
            
        # Real embeddings pass karein taaki dimensional AssertionError na aaye
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
                        
        logger.info("Search auto-suggestions route matched %d recommendations for query text: '%s'", len(matches), query)
    except Exception as e:
        logger.error("Failed to process auto-suggestions search items via FAISS: %s", str(e))
        return jsonify([])
        
    return jsonify(matches)
