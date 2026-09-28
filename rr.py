# 📍 FILE: app.py | Replace your _load_faq_index function with this version

from langchain_community.vectorstores import FAISS

def _load_faq_index() -> list[dict]:
    """🟢 CRASH-PROOF PRODUCTION LAYER: Loads genuine user questions directly 
    out of FAISS metadata and maps them strictly into your 4 pre-defined categories.
    Bypasses custom embedding imports to prevent ModuleNotFoundError.
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
        # 1. Check if the vector directory actually exists before calling loading modules
        if not os.path.exists(index_path):
            logger.warning("FAISS vector index repository directory not found at %s", index_path)
            return []
            
        # 2. Reconstruct the vector store metadata directly by passing a dummy embedding object.
        # Since we ONLY need to read string text content out of metadata fields, 
        # we don't need to trigger the actual Azure OpenAI neural network embedding calls!
        from langchain_core.embeddings import FakeEmbeddings
        fake_embeddings = FakeEmbeddings(size=1536) # Standard OpenAI vector dimension width
        
        vector_store = FAISS.load_local(index_path, fake_embeddings, allow_dangerous_deserialization=True)
        
        # 3. Extract internal document database dictionary structure securely
        docstore_dict = vector_store.docstore._dict
        
        # 4. Loop through vectors to gather clean question and category key records
        for doc_id, doc_obj in docstore_dict.items():
            metadata = doc_obj.metadata or {}
            text_value = doc_obj.page_content or ""
            
            # Extract basic text fields cleanly
            question_str = metadata.get("question") or text_value[:60]
            raw_category = str(metadata.get("category", "General")).strip().lower()
            
            # Category taxonomy assignment rules
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
                
        logger.info("Successfully populated %d suggestion entries straight from FAISS metadata.", len(entries))
    except Exception as e:
        logger.error("Failed to load metadata out of local index binary schema: %s", str(e))
        return []
        
    return entries

# Keeps your suggestion and autocomplete variables fully operational
FAQ_INDEX = _load_faq_index()
