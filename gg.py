"""FAISS cosine-similarity search over the chunk embeddings."""

import os
import json
import logging
from dotenv import load_dotenv
from src import config
from src.vectorstore.faiss_store import load_faiss_store_natively  # Accurate persistent db link
from langchain_core.tools import tool
from langchain_openai import AzureOpenAIEmbeddings

# Load credentials directly from your active configuration .env file
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

_embeddings_instance = None

def _get_active_embeddings():
    """Natively initializes the exact real embedding model from the environment,

    completely eliminating any 1536 dimension size mismatch errors.
    """
    global _embeddings_instance
    if _embeddings_instance is None:
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT") or os.getenv("AZURE_OPENAI_BASE_URL")
        azure_api_key = os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("AZURE_OPENAI_KEY")
        azure_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2023-05-15")
        
        # Target deployment setup configuration
        azure_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME") or os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME") or "text-embedding-ada-002"
        
        clean_endpoint = str(azure_endpoint).strip().rstrip('/') if azure_endpoint else ""
        clean_key = str(azure_api_key).strip() if azure_api_key else ""
        clean_version = str(azure_api_version).strip()
        clean_deployment = str(azure_deployment).strip()

        _embeddings_instance = AzureOpenAIEmbeddings(
            azure_endpoint=clean_endpoint,
            azure_deployment=clean_deployment,
            openai_api_key=clean_key,
            openai_api_version=clean_version
        )
    return _embeddings_instance


def retrieve(query: str, top_k: int = config.FINAL_TOP_K) -> list[dict]:
    """🟢 FINAL CRASH-PROOF ENGINE:

    Streams chunks directly out of binary FAISS repository using real embedding dimensions.
    """
    if not query.strip():
        return []
        
    try:
        # 1. Fetch real active embeddings signature instances model from env
        embeddings = _get_active_embeddings()
        
        # 2. Open the single-repository database binary files cache maps
        vector_store = load_faiss_store_natively(embeddings)
        if not vector_store:
            logger.error("❌ RETRIEVAL HALTED: FAISS index store structure failed to load.")
            return []
            
        # 3. Execute dense vector similarity mathematical matching algorithms
        logger.info("Executing vector scan logic for parameter query text: '%s'", query)
        raw_results = vector_store.similarity_search_with_score(query, k=top_k)
        
        formatted_chunks = []
        for doc, score in raw_results:
            # LangChain FAISS distance conversion formula layer to map standard L2 scores to standard 0.0 - 1.0 ranges
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
    
    if not hits or not isinstance(hits, list) or len(hits) == 0:
        return json.dumps([])
        
    # Grab the top search record correctly from the array list
    top_hit = hits[0]
    metadata = top_hit.get("metadata", {})
    
    is_xlsx = metadata.get("file_type") == "xlsx" or str(metadata.get("source", "")).lower().endswith(('.xlsx', '.xls'))
    mapped_answer = metadata.get("answer")
    
    target_threshold = getattr(config, "DIRECT_ANSWER_MIN_SCORE", 0.7)
    
    if is_xlsx and mapped_answer and float(top_hit.get("score", 0.0)) >= target_threshold:
        return f"[EXCEL_FAQ_DIRECT_HIT] {json.dumps(top_hit)}"
        
    return json.dumps(hits)
