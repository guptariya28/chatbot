"""FAISS cosine-similarity search over the chunk embeddings wrapped as a LangGraph Tool."""

import logging
import json
from src import config
from src.embedding.embedder import embed_text
from src.vectorstore.faiss_store import load_index, search as faiss_search
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

@tool
def retrieve_knowledge_base(query: str) -> str:
    """Search across the corporate financial dataset (FAQs, Word docs, and PDFs)."""
    hits = retrieve(query)
    if not hits:
        return json.dumps([])
    
    # Early Exit Check: Test if the absolute top hit matches Excel FAQ row parameters
    if isinstance(hits, list) and len(hits) > 0:
        top_hit = hits[0]
        metadata = top_hit.get("metadata", {})
        
        # Loader metadata check safely mapped matching your schema tags
        is_xlsx = metadata.get("file_type") == "xlsx" or str(metadata.get("source", "")).lower().endswith(('.xlsx', '.xls'))
        mapped_answer = metadata.get("answer")
        
        if is_xlsx and mapped_answer and top_hit.get("score", 0.0) >= 0.85:
            return f"[EXCEL_FAQ_DIRECT_HIT] {json.dumps(hits)}"
            
    return json.dumps(hits)
