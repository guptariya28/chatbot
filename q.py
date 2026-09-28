from langchain_core.messages import ToolMessage, AIMessage
 
def repair_history(messages):
    answered = {m.tool_call_id for m in messages if isinstance(m, ToolMessage)}
    fixed = []
    for m in messages:
        fixed.append(m)
        if isinstance(m, AIMessage) and m.tool_calls:
            for tc in m.tool_calls:
                if tc["id"] not in answered:
                    fixed.append(ToolMessage(
                        content="Tool call was interrupted.",
                        tool_call_id=tc["id"],
                    ))
    return fixed
