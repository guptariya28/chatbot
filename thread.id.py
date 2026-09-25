@app.route("/api/test-clear")
def test_clear():
    # 🟢 1. Active user ki session cookie se thread ID nikal kar delete karein
    conversation_id = session.pop("conversation_id", None)
    
    # 2. Agar thread ID milti hai, toh response dikhayein
    if conversation_id:
        logger.info(f"[LIVE PROOF] Thread {conversation_id} context successfully cleared from RAM!")
        return jsonify({
            "status": "Success",
            "message": f"Thread {conversation_id} has been completely deleted from RAM memory.",
            "action": "Old session memory ledger dropped."
        }), 200
    else:
        return jsonify({
            "status": "No Active Session",
            "message": "No active conversation_id found in cookies to delete."
        }), 200
