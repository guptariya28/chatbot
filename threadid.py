@app.route("/api/ask", methods=["POST"])
def ask():
    body = request.get_json(force=True) or {}
    question = body.get("question", "").strip()
    
    # 🟢 A. HARDCODE THE TARGET USER ID (As requested for your validation checks)
    HARDCODED_USER_ID = "user_employee_101"
    
    # 🟢 B. DYNAMIC FLASK SESSION THREAD TRACKER:
    # If this specific browser environment doesn't have an active chat trail yet,
    # generate a unique, random string specifically for this active session window.
    if "conversation_id" not in session:
        session["conversation_id"] = f"thread_{uuid.uuid4().hex[:8]}"
        
    conversation_id = session["conversation_id"]
    
    if not question:
        return jsonify({"error": "question is required"}), 400

    # Bind the Flask session's isolated ID right into LangGraph's engine checkpoint
    config_thread = {"configurable": {"thread_id": conversation_id}}
    initial_state = {"messages": [HumanMessage(content=question)]}
    
    # Log diagnostic details to your console terminal window for live verification checks
    logger.info(f"=== [MULTI-USER LOG] ID Verification Handshake ===")
    logger.info(f"User Profile Mapped: {HARDCODED_USER_ID}")
    logger.info(f"Active Client Environment Thread: {conversation_id}")
    
    try:
        output_state = graph_agent.invoke(initial_state, config=config_thread)
        last_ai_message = output_state["messages"][-1].content
        payload_data = output_state.get("final_payload", {})
        raw_sources = payload_data.get("sources", [])
    except Exception as e:
        logger.error(f"Graph invocation error: {str(e)}")
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
        "user_id": HARDCODED_USER_ID, # Returning details to frontend metrics panels
        "message_id": mock_msg_id
    })
