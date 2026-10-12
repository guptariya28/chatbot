@app.route("/api/copilot/ask", methods=["POST"])
def copilot_ask():

    try:
        # 1. Get request data
        body = request.get_json(silent=True) or {}

        question = body.get("question", "").strip()

        # 2. Validate question
        if not question:
            return jsonify({
                "error": "question is required"
            }), 400

        # 3. Get or generate conversation ID
        conversation_id = body.get("conversation_id")

        if not conversation_id:
            conversation_id = f"copilot_{uuid.uuid4().hex[:16]}"

        # 4. Configure LangGraph thread
        config_thread = {
            "configurable": {
                "thread_id": conversation_id
            }
        }

        # 5. Prepare initial state
        initial_state = {
            "messages": [
                HumanMessage(content=question)
            ]
        }

        # 6. Invoke existing LangGraph agent
        output_state = graph_agent.invoke(
            initial_state,
            config=config_thread
        )

        # 7. Extract answer
        answer = output_state["messages"][-1].content

        # 8. Extract sources and metadata
        payload_data = output_state.get("final_payload", {})
        raw_sources = payload_data.get("sources", [])

        formatted_sources = _format_sources(raw_sources)

        # 9. Return successful response
        return jsonify({
            "answer": answer,
            "sources": formatted_sources,
            "conversation_id": conversation_id
        }), 200

    except Exception as e:

        # Log complete exception and traceback
        app.logger.exception("Copilot API failed")

        # Return error details for debugging
        return jsonify({
            "error": "Unable to process the question.",
            "details": str(e)
        }), 500
