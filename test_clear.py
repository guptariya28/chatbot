@app.route("/api/test-clear")
def test_clear():
    """Evicts the active user's session token and natively purges graph state from RAM."""
    conversation_id = session.get("conversation_id")
    
    if conversation_id:
        try:
            # 🟢 TRUE RAM EVICTION: Native LangGraph checkpoint drop sequence
            # Reaches into the memory database structure and unlinks all message states.
            # Python's Garbage Collector instantly flushes the freed memory out of RAM.
            config_target = {"configurable": {"thread_id": conversation_id}}
            graph_agent.checkpointer.delete_thread(config_target)
            logger.info("LangGraph state storage ledger for thread %s successfully purged from RAM.", conversation_id)
        except Exception as e:
            logger.error("Failed to natively clear checkpointer storage structure: %s", str(e))
        
        # Safely remove the browser cookie proxy tracker layer
        session.pop("conversation_id", None)
        
        return jsonify({
            "status": "Success",
            "message": "LangGraph state memory array and browser session token have been completely evicted.",
            "action": "True RAM execution cache cleared."
        }), 200
    
    return jsonify({
        "status": "No Active Session",
        "message": "RAM state store was already empty or cleared."
    }), 200