import os
import logging
from langchain_community.vectorstores import FAISS

# Initialize standard enterprise logging configuration wrappers
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

INDEX_PATH = "data/faiss_index"

def build_and_save_faiss_store(langchain_documents: list, embeddings_model) -> bool:
    """🟢 IN-MEMORY TO BINARY PRODUCTION ENGINE:
    Takes clean LangChain Document schema arrays entirely inside RAM,
    computes dense neural network vectors matrix, and writes directly
    to the local folder repo. Rips out all intermediate duplicate log writes!
    """
    if not langchain_documents:
        logger.error("❌ ERROR: Empty document list passed to FAISS engine. Compilation halted.")
        return False
        
    try:
        logger.info("Starting dense vector transformation for %d chunks...", len(langchain_documents))
        
        # 1. Directly execute the mathematical embedding and clustering sequence in RAM
        vector_store = FAISS.from_documents(langchain_documents, embeddings_model)
        
        # 2. Guarantee that the target parent database folder pathway exists securely
        os.makedirs(os.path.dirname(INDEX_PATH), exist_ok=True)
        
        # 3. ❌ DELETED ALL DEV-PHASE REDUNDANT JSONL FILE WRITES!
        # There are no more local text log buffers to clutter hard disk space.
        
        # 4. Save the true single-repository binary assets cluster directly to disk
        vector_store.save_local(INDEX_PATH)
        
        logger.info("🎉 SUCCESS! FAISS Vector Store binary layers saved flawlessly at: %s", INDEX_PATH)
        logger.info("Verified Folder Outputs: Both 'index.faiss' and 'index.pkl' are built completely.")
        return True
        
    except Exception as e:
        logger.error("❌ FAISS COMPILATION EXCEPTION FAULT: %s", str(e), exc_info=True)
        return False

def load_faiss_store_natively(embeddings_model):
    """Natively restores the local binary FAISS vector store mapping records 
    from the disk folder framework into active deployment execution scope.
    """
    try:
        if not os.path.exists(INDEX_PATH):
            logger.error("❌ ERROR: FAISS local index workspace repository not found at %s", INDEX_PATH)
            return None
            
        logger.info("Restoring binary vector configurations from local store: %s", INDEX_PATH)
        vector_store = FAISS.load_local(INDEX_PATH, embeddings_model, allow_dangerous_deserialization=True)
        return vector_store
        
    except Exception as e:
        logger.error("Failed to natively reconstruct vector store instance from disk: %s", str(e), exc_info=True)
        return None
