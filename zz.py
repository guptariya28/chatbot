"""FAISS cosine-similarity search over the chunk embeddings."""

import os
import json
import logging
from src import config
from src.vectorstore.faiss_store import load_faiss_store_natively  # 🟢 INTERFACE HOOK CONNECTED NATIVELY
from langchain_core.tools import tool
from langchain_openai import AzureOpenAIEmbeddings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Initialize dynamic neural networks embeddings once for the active search scope
_embeddings_instance = None

def _get_active_embeddings():
    """Natively retrieves or initializes aligned embeddings out of the active environment configuration."""
    global _embeddings_instance
    if _embeddings_instance is None:
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT") or os.getenv("AZURE_OPENAI_BASE_URL")
        azure_api_key = os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("AZURE_OPENAI_KEY")
        azure_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2023-05-15")
        azure_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME") or os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        
        _embeddings_instance = AzureOpenAIEmbeddings(
            azure_endpoint=str(azure_endpoint).strip() if azure_endpoint else "",
            azure_deployment=str(azure_deployment).strip() if azure_deployment else "text-embedding-ada-002",
            openai_api_key=str(azure_api_key).strip() if azure_api_key else "",
            openai_api_version=str(azure_api_version).strip()
        )
    return _embeddings_instance


def retrieve(query: str, top_k: int = config.FINAL_TOP_K) -> list[dict]:
    """🟢 IN-MEMORY RETRIEVAL ENGINE:
    Natively streams text chunks directly out of the binary FAISS folder repository.
    Converts L2 distance to normalized similarity to pass threshold scores gracefully.
    """
    if not query.strip():
        return []
        
    try:
        # 1. Fetch real active embeddings signature instances model from env
        embeddings = _get_active_embeddings()
        
        # 2. Open the single-repository database binary files cache maps
        vector_store = load_faiss_store_natively(embeddings)
        if not vector_store:
            logger.error("❌ RETRIEVAL HALTED: FAISS index store structure failed to load into server context.")
            return []
            
        # 3. Execute dense vector similarity mathematical matching algorithms
        logger.info("Executing vector scan logic for parameter query text: '%s'", query)
        raw_results = vector_store.similarity_search_with_score(query, k=top_k)
        
        # 4. Formulate standardized text chunk configurations payload matrices
        formatted_chunks = []
        for doc, score in raw_results:
            # LangChain FAISS distance conversion formula layer:
            # Maps standard L2 metric scores securely back into a 0.0 - 1.0 range,
            # ensuring your score >= 0.7 target threshold conditions evaluate perfectly!
            cosine_sim = 1.0 - (float(score) / 2.0) if float(score) <= 2.0 else 0.0
            
            formatted_chunks.append({
                "text": doc.page_content,
                "metadata": doc.metadata,
                "score": cosine_sim
            })
            
        logger.info("FAISS returned %d result(s) for query: %r", len(formatted_chunks), query)
        return formatted_chunks
        
    except Exception as e:
        logger.error("Failed to query vector database elements from retriever: %s", str(e), exc_info=True)
        return []


@tool
def retrieve_knowledge_base(query: str) -> str:
    """Search across the company financial warehouse (Excel FAQs, Word docs, and PDFs)."""
    hits = retrieve(query)
    
    # Validation check: Agar hits khali hain toh empty list string return karein
    if not hits or not isinstance(hits, list) or len(hits) == 0:
        return json.dumps([])
        
    # FIXED DATA EXTRACTION: Grab the absolute top hit at index 0 from the list
    top_hit = hits[0]
    metadata = top_hit.get("metadata", {})
    
    is_xlsx = metadata.get("file_type") == "xlsx" or str(metadata.get("source", "")).lower().endswith(('.xlsx', '.xls'))
    mapped_answer = metadata.get("answer")
    
    # Dynamic binding matching your screenshot config.py parameters cleanly
    target_threshold = getattr(config, "DIRECT_ANSWER_MIN_SCORE", 0.7)
    
    # Test conditions securely now
    if is_xlsx and mapped_answer and float(top_hit.get("score", 0.0)) >= target_threshold:
        # Pura list pass karein json structures me takki app.py use index kar sake
        return f"[EXCEL_FAQ_DIRECT_HIT] {json.dumps(top_hit)}"
        
    return json.dumps(hits)
