"""FAISS cosine-similarity search over the chunk embeddings wrapped as a LangGraph Tool."""

import logging
import json
from src import config
from src.embedding.embedder import embed_text
from src.vectorstore.faiss_store import load_index, search as faiss_search

# LangGraph runtime connection components
from langchain_core.tools import tool

logger = logging.getLogger(__name__)

_index = None
_chunks = None

def _get_index():
    global _index, _chunks
    if _index is None:
        _index, _chunks = load_index()
        logger.info("Loaded FAISS index with %d vectors", _index.ntotal)
    return _index, _chunks

def retrieve(query: str, top_k: int = config.FINAL_TOP_K) -> list[dict]:
    """Embed 'query' and return the top_k most similar chunks (with scores)."""
    index, chunks = _get_index()
    query_embedding = embed_text(query)
    results = faiss_search(index, chunks, query_embedding, top_k=top_k)
    logger.info("FAISS returned %d result(s) for query: %r", len(results), query)
    return results

# --------------------------------------------------------------------------
# LangGraph Core Architecture Tool Integration
# --------------------------------------------------------------------------
@tool
def retrieve_knowledge_base(query: str) -> str:
    """Search across the company financial warehouse (Excel FAQs, Word docs, and PDFs)."""
    # 1. Execute your existing vector search pipeline logic
    hits = retrieve(query)
    
    if not hits:
        return json.dumps([])
        
    # 2. Extract top priority hit details
    top_hit = hits[0] if isinstance(hits, list) and len(hits) > 0 else {}
    metadata = top_hit.get("metadata", {})
    
    # 3. ABSOLUTE EXCEL FAQ MATCHING RULE
    # Loader metadata sets "file_type": "xlsx" and extracts the direct "answer" column row
    is_xlsx = metadata.get("file_type") == "xlsx"
    mapped_answer = metadata.get("answer")
    
    # Validation threshold logic (e.g., strong semantic similarity matching score)
    if is_xlsx and mapped_answer and top_hit.get("score", 0.0) >= 0.85:
        # Prepend tracking token markers so app.py knows it can bypass the LLM completely
        return f"[EXCEL_FAQ_DIRECT_HIT] {json.dumps(hits)}"
        
    # 4. Standard fallback response for document chunks (PDF/Docx/Low-Score Excel)
    return json.dumps(hits)
