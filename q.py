s
from langchain_community.vectorstores import FAISS
from langchain_core.embeddings import FakeEmbeddings

# Logger instance tracking configurations
logger = logging.getLogger(__name__)

# 🟢 GLOBAL CONFIGURATION: Pre-defined Production Corporate Taxonomy Namespaces
ALLOWED_CATEGORIES = {
    "accounts payable", 
    "corporate credit card", 
    "food", 
    "reimbursement account"
}
INDEX_PATH = "data/faiss_index"


@app.route("/api/categories")
def get_categories():
    """Returns strictly the 4 pre-defined corporate category metadata buckets to the UI panel layout."""
    # Production layout metrics: Hardcoded keys lock the button visibility controls permanently.
    predefined_counts = {
        "Accounts Payable": 1,
        "Corporate Credit Card": 1,
        "Food": 1,
        "Reimbursement Account": 1
    }
    logger.info("Delivered fixed 4 corporate categories array dictionary to frontend UI dashboard panel.")
    return jsonify(predefined_counts)


@app.route("/api/categories/<category>/questions")
def get_category_questions(category: str):
    """Fetches genuine suggestion questions directly from the FAISS local database metadata matching this active label."""
    # URL encoded space extraction protocol check (%20 replacement logic)
    target_category = category.replace("%20", " ").strip().lower()
    matches = []
    
    try:
        if not os.path.exists(INDEX_PATH):
            logger.warning("FAISS local index workspace repository not found at %s", INDEX_PATH)
            return jsonify([])
            
        # Reconstruct the vector store database registry map cleanly without calling remote web APIs
        fake_embeddings = FakeEmbeddings(size=1536)
        vector_store = FAISS.load_local(INDEX_PATH, fake_embeddings, allow_dangerous_deserialization=True)
        docstore_dict = vector_store.docstore._dict
        
        # Scan vectors metadata registries to filter and gather questions matching this category button turn
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
                
        logger.info("Category matching routine successfully loaded %d question options for target path: %s", len(matches), category)
    except Exception as e:
        logger.error("Failed to dynamically read category question lists from FAISS registry layers: %s", str(e), exc_info=True)
        return jsonify([])
        
    return jsonify(matches)


@app.route("/api/suggestions")
def get_suggestions():
    """Returns dynamic autocomplete search queries parsed live from the FAISS vector store binary file metadata caching."""
    query = request.args.get("q", "").strip().lower()
    
    # Performance Guard Control Switch: Avoid parsing loop costs for minimal string updates
    if len(query) < 2:
        return jsonify([])
        
    matches = []
    SUGGESTIONS_LIMIT = 5  # Production layout cap threshold limits
    
    try:
        if not os.path.exists(INDEX_PATH):
            return jsonify([])
            
        # Extract binary vector layout entries into active execution processing scope
        fake_embeddings = FakeEmbeddings(size=1536)
        vector_store = FAISS.load_local(INDEX_PATH, fake_embeddings, allow_dangerous_deserialization=True)
        docstore_dict = vector_store.docstore._dict
        
        # Evaluate overlaps across question string contents and valid taxonomy namespaces
        for doc_id, doc_obj in docstore_dict.items():
            metadata = doc_obj.metadata or {}
            text_value = doc_obj.page_content or ""
            
            raw_category = str(metadata.get("category", "General")).strip().lower()
            
            if raw_category in ALLOWED_CATEGORIES:
                question_text = str(metadata.get("question") or text_value[:60]).strip()
                
                # Evaluation condition rules (Matches typing query string inside question text OR category phrase)
                if query in question_text.lower() or query in raw_category:
                    # Uniform display casing adjustments for frontend drop containers
                    formatted_category = raw_category.title()
                    if raw_category == "corporate credit card":
                        formatted_category = "Corporate Credit Card"
                        
                    matches.append({
                        "question": question_text,
                        "category": formatted_category,
                        "source": str(metadata.get("source", ""))
                    })
                    
                    # Early termination trigger to maximize background network speedups
                    if len(matches) >= SUGGESTIONS_LIMIT:
                        break
                        
        logger.info("Autocomplete search endpoint matched %d option recommendations for user parameter query: '%s'", len(matches), query)
    except Exception as e:
        logger.error("Failed to accurately filter search index recommendations from FAISS metadata loops: %s", str(e), exc_info=True)
        return jsonify([])
        
    return jsonify(matches)
