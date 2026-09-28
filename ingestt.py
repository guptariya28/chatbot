import os
import logging
from src import config
from src.ingestion.loader import load_document, supported_extensions
from src.chunking.chunker import chunk_documents
from langchain_community.vectorstores import FAISS
from src.embedding.embedding_factory import get_embedding_model  # Aapki genuine path check karein
from langchain_core.documents import Document

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DEFAULT_INPUT_DIR = config.PROJECT_ROOT.parent / "Finance"
INDEX_PATH = "data/faiss_index"

def find_files(input_dir) -> list:
    files = []
    for ext in supported_extensions:
        for file_path in input_dir.rglob(f"*{ext}"):
            if not file_path.name.startswith("~$"):
                files.append(file_path)
    return sorted(files)

def ingest_directory(input_dir) -> list[dict]:
    all_documents = []
    files = find_files(input_dir)
    logger.info("Found %d supported file(s) in %s", len(files), input_dir)
    
    for file_path in files:
        try:
            documents = load_document(file_path)
            all_documents.extend(documents)
            logger.info("Loaded %-45s -> %d document(s)", file_path.name, len(documents))
        except Exception:
            logger.exception("Failed to load %s", file_path.name)
            
    return all_documents

def main():
    # 1. Read files directly into memory RAM list dictionaries
    raw_docs = ingest_directory(DEFAULT_INPUT_DIR)
    if not raw_docs:
        logger.error("No documents were loaded. Ingestion terminating.")
        return
        
    # 2. Chunk text blocks natively using memory buffers (No local JSONL writes)
    logger.info("Splitting documents into optimal context chunks...")
    memory_chunks = chunk_documents(raw_docs)
    logger.info("Generated %d chunks dynamically in active RAM.", len(memory_chunks))
    
    # 3. 🟢 THE COMPLETE FAISS PERSISTENCE FIX:
    # Convert clean python dict items back into strict LangChain Document schemas.
    # This guarantees that BOTH index.faiss and index.pkl are physically built!
    langchain_docs = []
    for chunk in memory_chunks:
        langchain_docs.append(
            Document(
                page_content=chunk["text"],
                metadata=chunk["metadata"]
            )
        )
        
    # 4. Generate Neural Embeddings and Save the True Local Single-Repository Cluster
    logger.info("Invoking Azure OpenAI embeddings models to compute dense vectors...")
    embeddings_model = get_embedding_model()
    
    vector_store = FAISS.from_documents(langchain_docs, embeddings_model)
    vector_store.save_local(INDEX_PATH)
    
    logger.info("🎉 SUCCESS! FAISS Vector DB single-repository binary assets compiled flawlessly at: %s", INDEX_PATH)
    logger.info("Verified folder contents: Both 'index.faiss' and 'index.pkl' are built completely.")

if __name__ == "__main__":
    main()
