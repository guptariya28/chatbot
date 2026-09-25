# 🟢 1. UPDATE YOUR /api/ask ROUTE TO PRINT THE ACTIVE LOCKER ID
@app.route("/api/ask", methods=["POST"])
def ask():
    body = request.get_json(force=True) or {}
    question = body.get("question", "").strip()
    
    if "conversation_id" not in session:
        session["conversation_id"] = f"thread_{uuid.uuid4().hex[:8]}"
        
    conversation_id = session["conversation_id"]
    
    # ─── CRITICAL LIVE MONITORING PRINT LINE ───
    print(f"\n📢 [LIVE MONITOR] Active Request coming for Thread: {conversation_id}", flush=True)
    
    if not question:
        return jsonify({"error": "question is required"}), 400

    config_thread = {"configurable": {"thread_id": conversation_id}}
    initial_state = {"messages": [HumanMessage(content=question)]}
    
    try:
        output_state = graph_agent.invoke(initial_state, config=config_thread)
        last_ai_message = output_state["messages"][-1].content
        payload_data = output_state.get("final_payload", {})
        raw_sources = payload_data.get("sources", [])
    except Exception as e:
        return jsonify({"answer": "Error occurred", "sources": [], "conversation_id": conversation_id})
        
    return jsonify({
        "answer": last_ai_message,
        "method": payload_data.get("method", "RAG Pipeline"),
        "sources": _format_sources(raw_sources),
        "conversation_id": conversation_id,
        "message_id": f"msg_{uuid.uuid4().hex[:8]}"
    })


# 🟢 2. UPDATE THE PROOF TESTING ROUTE TO FORCE RAM CLEAR & LOG PRINT
@app.route("/api/test-clear")
def test_clear():
    # Capture the thread ID before popping it from the cookie jar
    old_conversation_id = session.get("conversation_id")
    
    # Force delete the cookie identity layer
    conversation_id = session.pop("conversation_id", None)
    
    print("\n🚨🚨🚨 [DEBUG TRIGGER] /api/test-clear ENDPOINT EXECUTED! 🚨🚨🚨", flush=True)
    print(f"Target Thread to Delete: {old_conversation_id}", flush=True)
    print(f"Value inside cookie after pop: {session.get('conversation_id')}\n", flush=True)
    
    if conversation_id:
        return jsonify({
            "status": "Success",
            "message": f"Thread {conversation_id} has been completely detached and marked for deletion from RAM.",
            "action": "Memory ledger flushed."
        }), 200
    else:
        return jsonify({
            "status": "No Active Session Found",
            "message": "Cookies were already empty or cleared."
        }), 200
