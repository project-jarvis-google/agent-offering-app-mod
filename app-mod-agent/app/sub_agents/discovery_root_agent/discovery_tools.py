from google.adk.tools import ToolContext

def save_user_intent(intent_summary: str, tool_context: ToolContext) -> bool:
    """
    Saves the user's migration intent summary to the shared state.
    """
    tool_context.state["user_intent"] = intent_summary
    return True
