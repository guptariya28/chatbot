# 📍 Add SystemMessage to your langchain_core imports at the top of the file:
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage

# 🟢 UPDATE INSIDE agent_node:
def agent_node(state: AgentState) -> dict:
    # Change your SYSTEM_PROMPT container to use SystemMessage natively:
    SYSTEM_PROMPT = SystemMessage(
        content=(
            "You are a finance helpdesk assistant. Answer the user's question "
            "using ONLY the context provided below. If the context does not "
            "contain enough information to answer, say so clearly instead of "
            "guessing. Keep answers concise and answer directly - do not start "
            "with a greeting like 'Hello' or 'Hi'. Do not cite or mention source "
            "file names in your answer text; sources are shown separately in the "
            "UI, so never write things like '(Source: ...)'. "
        )
    )
    
    raw_messages = list(state["messages"])
    WINDOW_SIZE = 6
    if len(raw_messages) > WINDOW_SIZE:
        candidate_messages = raw_messages[-WINDOW_SIZE:]
        while candidate_messages and (
            isinstance(candidate_messages[0], ToolMessage) or
            (isinstance(candidate_messages[0], AIMessage) and candidate_messages[0].tool_calls)
        ):
            candidate_messages = candidate_messages[1:]
        messages = candidate_messages
    else:
        messages = raw_messages

    formatted_messages = []
    for msg in messages:
        if msg.type == "system":
            continue
        if isinstance(msg, ToolMessage):
            try:
                raw_hits = json.loads(msg.content)
                blocks = []
                for i, chunk in enumerate(raw_hits):
                    src_name = chunk.get('metadata', {}).get('source', 'unknown')
                    blocks.append(f"[{i + 1}] (Source: {src_name})\n{chunk.get('text', '')}")
                context_string = "\n\n".join(blocks)
                
                formatted_messages.append(ToolMessage(
                    content=f"Context:\n{context_string}\n\nAnswer using only the context above.",
                    tool_call_id=msg.tool_call_id,
                    name=msg.name
                ))
            except Exception:
                formatted_messages.append(msg)
        else:
            formatted_messages.append(msg)

    # 🟢 FIXED FINAL INPUT STREAM LAYER:
    # Prepend the strict SystemMessage object. The history chain now alternates perfectly!
    final_input_stream = [SYSTEM_PROMPT] + formatted_messages
    response = llm_with_tools.invoke(final_input_stream)
    
    if response.content:
        response.content = SOURCE_CATION_PATTERN.sub("", response.content).strip()
        
    return {"messages": [response]}
