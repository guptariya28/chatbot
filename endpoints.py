@app.route("/api/ask", methods=["POST"])
def ask():
    """Exposes a JSON REST API endpoint to invoke the external LangGraph engine with SQLite storage."""
    body = request.get_json(force=True) or {}
    question = body.get("question", "").strip()
    
    # Establish or read a secure, isolated cookie-based conversation identifier
    if "conversation_id" not in session:
        session["conversation_id"] = f"thread_{uuid.uuid4().hex[:8]}"
        
    conversation_id = session["conversation_id"]
    
    if not question:
        return jsonify({"error": "question is required"}), 400

    # Bind the session token into LangGraph's configuration schema
    config_thread = {"configurable": {"thread_id": conversation_id}}
    initial_state = {"messages": [HumanMessage(content=question)]}
    
    try:
        # Trigger the modular state graph flowchart execution loop
        output_state = graph_agent.invoke(initial_state, config=config_thread)
        last_ai_message = output_state["messages"][-1].content
        payload_data = output_state.get("final_payload", {})
        raw_sources = payload_data.get("sources", [])
    except Exception as e:
        logger.error("Graph invocation exception error: %s", str(e), exc_info=True)
        return jsonify({
            "answer": "An internal graph execution error occurred. Please try again.",
            "method": "Error Fallback",
            "sources": [],
            "conversation_id": conversation_id
        })
    
    mock_msg_id = f"msg_{uuid.uuid4().hex[:8]}"
    return jsonify({
        "answer": last_ai_message,
        "method": payload_data.get("method", "RAG Pipeline (Azure OpenAI Synth)"),
        "sources": _format_sources(raw_sources),
        "conversation_id": conversation_id,
        "message_id": mock_msg_id
    })


@app.route("/api/test-clear")
def test_clear():
    """Natively purges conversation thread state records from the SQLite database and evicts cookies."""
    conversation_id = session.get("conversation_id")
    
    if conversation_id:
        try:
            # 🟢 PERSISTENT DISK PURGE:
            # This calls the SQLite checkpointer interface layer to physically delete 
            # all rows, snapshots, and checkpoints matching this specific thread_id from the disk.
            config_target = {"configurable": {"thread_id": conversation_id}}
            graph_agent.checkpointer.delete_thread(config_target)
            logger.info("LangGraph SQLite checkpointer logs for thread %s successfully purged from disk database.", conversation_id)
        except Exception as e:
            logger.error("Failed to execute native SQLite checkpointer state eviction: %s", str(e))
        
        # Evict the client-side browser session tracking key cookie
        session.pop("conversation_id", None)
        
        return jsonify({
            "status": "Success",
            "message": "LangGraph SQLite persistent rows and browser session tokens have been completely evicted.",
            "action": "True database storage clean complete."
        }), 200
        
    return jsonify({
        "status": "No Active Session",
        "message": "SQLite checkpointer layer was already clean or empty."
    }), 200
