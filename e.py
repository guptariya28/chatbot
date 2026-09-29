import sqlite3
# This is LangGraph's built-in serializer to unpack the binary data
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

DB_PATH = r"C:\Users\ashvish\My Notebook\Use Case 2026\Finance Chatot\rag_chatbott_latest_working\chat_history.db"
serializer = JsonPlusSerializer()

# Connect and grab the checkpoints
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute("SELECT thread_id, checkpoint FROM checkpoints")
rows = cursor.fetchall()
conn.close()

print(f"--- Printing Chat Logs for {len(rows)} Checkpoints ---\n")

for thread_id, raw_checkpoint in rows:
    try:
        # Unpack the binary checkpoint into a readable dictionary
        checkpoint_dict = serializer.loads(raw_checkpoint)
        
        # Pull out the channel data where messages live
        channel_values = checkpoint_dict.get("channel_values", {})
        messages = channel_values.get("messages", [])
        
        if messages:
            print(f"🧵 [Thread ID: {thread_id}]")
            for msg in messages:
                # Check the class name or type of the message
                msg_type = type(msg).__name__ if hasattr(msg, '__class__') else "Message"
                
                # Extract role and content safely
                if hasattr(msg, 'content'):
                    content = msg.content
                elif isinstance(msg, dict):
                    content = msg.get('content', '')
                else:
                    content = str(msg)
                
                # Format based on who sent it
                if "Human" in msg_type or getattr(msg, 'type', '') == 'human':
                    print(f"👤 User: {content}")
                elif "AI" in msg_type or getattr(msg, 'type', '') == 'ai':
                    print(f"🤖 AI  : {content}")
            print("-" * 60)
            
    except Exception as e:
        # Fallback if a specific row has a parsing issue
        print(f"Could not parse checkpoint for thread {thread_id}: {e}")
