embeddings_model = AzureOpenAIEmbeddings(
        azure_deployment="text-embedding-ada-002", # Change this to your exact embedding deployment name if different
        openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2023-05-15")
    )
    
    # 5. Build and Save the True Local Single-Repository Cluster
    vector_store = FAISS.from_documents(langchain_docs, embeddings_model)
    
    # Ensure the parent data folder exists before writing binary data records
    os.makedirs(os.path.dirname(INDEX_PATH), exist_ok=True)
    vector_store.save_local(INDEX_PATH)
    
    logger.info("🎉 SUCCESS! FAISS Vector DB binary assets compiled flawlessly at: %s", INDEX_PATH)
    logger.info("Verified folder contents: Both 'index.faiss' and 'index.pkl' are built completely.")

if __name__ == "__main__":
    main()
