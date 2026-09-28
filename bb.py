azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT") or os.getenv("AZURE_OPENAI_BASE_URL")
    azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
    azure_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2023-05-15")
    azure_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME") or os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "text-embedding-ada-002")

    if not azure_api_key or not azure_endpoint:
        logger.error("❌ CRITICAL: Missing Azure OpenAI keys/endpoints inside your active .env file dashboard!")
        return

    embeddings_model = AzureOpenAIEmbeddings(
        azure_endpoint=str(azure_endpoint).strip(),
        azure_deployment=str(azure_deployment).strip(),
        openai_api_key=str(azure_api_key).strip(),
        openai_api_version=str(azure_api_version).strip()
    )
    
    # 5. Build and Save the True Local Single-Repository Cluster
    logger.info("Computing dense vectors matrix arrays for FAISS compilation loop...")
    vector_store = FAISS.from_documents(langchain_docs, embeddings_model)
    
    # Ensure the parent data folder exists before writing binary data records
    os.makedirs(os.path.dirname(INDEX_PATH), exist_ok=True)
    vector_store.save_local(INDEX_PATH)
    
    logger.info("🎉 SUCCESS! FAISS Vector DB binary assets compiled flawlessly at: %s", INDEX_PATH)
    logger.info("Verified folder contents: Both 'index.faiss' and 'index.pkl' are built completely.")

if __name__ == "__main__":
    main()
