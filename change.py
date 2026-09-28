from langchain_community.vectorstores import FAISS
from src.embedding.embedding_factory import get_embedding_model  # Aapki embedding function file check karein

def _load_faq_index() -> list[dict]:
    """🟢 PRODUCTION OPTIMIZED: Loads genuine user questions directly out of 
    FAISS metadata and maps them strictly into your 4 pre-defined corporate categories.
    """
    # Strict Corporate taxonomy definitions
    ALLOWED_CATEGORIES = {
        "accounts payable", 
        "corporate credit card", 
        "food", 
        "reimbursement account"
    }
    
    entries = []
    index_path = "data/faiss_index"
    
    try:
        # 1. Reconstruct the vector store asset directly out of local disk storage
        embeddings = get_embedding_model()
        vector_store = FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)
        
        # 2. Extract internal document database dictionary structure securely
        docstore_dict = vector_store.docstore._dict
        
        # 3. Loop through vectors to gather clean question and category key records
        for doc_id, doc_obj in docstore_dict.items():
            metadata = doc_obj.metadata or {}
            text_value = doc_obj.page_content or ""
            
            # Extract basic text fields cleanly
            question_str = metadata.get("question") or text_value[:60]
            raw_category = str(metadata.get("category", "General")).strip().lower()
            
            # 🟢 CATEGORY FILTER OVERRIDE:
            # Agar vector data ki category in 4 rules me se match nahi karti, 
            # toh production standard ke liye hum use 'General' ya drop karne ke bajaye skip kar sakte hain,
            # ya ensure kar sakte hain ki wahi aayen jo list me hain.
            if raw_category in ALLOWED_CATEGORIES:
                # Proper format string naming for UI dropdown display panel
                formatted_category = raw_category.title()
                if raw_category == "corporate credit card":
                    formatted_category = "Corporate Credit Card"
                    
                entries.append({
                    "question": str(question_str).strip(),
                    "category": formatted_category,
                    "source": str(metadata.get("source", ""))
                })
                
        logger.info("Natively populated %d active suggestion queries straight from FAISS Index.", len(entries))
    except Exception as e:
        logger.error("Failed to extract categories from local index binary schema: %s", str(e))
        return []
        
    return entries

# The global pointer array stays 100% active for the rest of your app routes
FAQ_INDEX = _load_faq_index()


@app.route("/api/suggestions")
def get_suggestions():
    """Returns dynamic autocomplete search queries matched against the FAISS index payload."""
    query = request.args.get("q", "").strip().lower()
    
    # If the user has typed less than 2 characters, don't waste compute cycles
    if len(query) < 2:
        return jsonify([])
        
    matches = []
    SUGGESTIONS_LIMIT = 5 # Production layout standard capping threshold
    
    for entry in FAQ_INDEX:
        question_text = entry["question"].lower()
        category_text = entry["category"].lower()
        
        # Filter matching conditions (Matches query inside question text OR category name)
        if query in question_text or query in category_text:
            matches.append({
                "question": entry["question"],
                "category": entry["category"],
                "source": entry["source"]
            })
            if len(matches) >= SUGGESTIONS_LIMIT:
                break
                
    return jsonify(matches)
