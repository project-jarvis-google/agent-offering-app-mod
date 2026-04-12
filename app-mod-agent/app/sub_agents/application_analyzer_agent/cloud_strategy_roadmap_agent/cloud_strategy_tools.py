import logging
from google.adk.tools import ToolContext
from ..utils.gemini_utils import analyze_codebase_with_gemini

async def perform_cloud_strategy_analysis(tool_context: ToolContext) -> bool:
    """
    Analyzes the codebase and generates cloud strategy and roadmap.
    """
    secure_temp_repo_dir = tool_context.state.get("secure_temp_repo_dir")
    if not secure_temp_repo_dir:
        logging.error("No codebase directory found in state.")
        return False
        
    prompt = """
    Analyze the cloud readiness of this application based on the supplied codebase. 
    Do NOT provide generic guidance. Provide a concrete, actionable modernization strategy and roadmap covering:

    1. **Modernization Strategy & Options (The 5 R's)**: 
       * Recommend whether to **Rehost**, **Refactor**, or **Rearchitect** specific distinct components, citing the code paths influencing your decision.
       * For each major component (e.g., Computing, Database, Messaging), highlight all viable **Google Cloud solutions** (e.g., GKE vs Cloud Run vs App Engine for computing).
       * Provide a **Pros & Cons breakdown** for alternative GCP service targets, weighing them specifically for *this* codebase layout.

    2. **Resource Mapping with Reasoning**: 
       * Map internal resources to standard GCP counterparts.
       * Support the recommendation with architectural reasoning (e.g., "We recommend Cloud Run over GKE because this workload is stateless and scales well independently").

    3. **Migration Blockers & Remediation**: 
       * Call out hard-coded absolute paths, tightly coupled localhost bindings, or hardcoded IPs that will block containerization.
       * For these blockers, provide simple code examples showing the current problematic code and a suggested remediation (e.g., using environment variables or configuration files) in standard markdown `diff` format.

    4. **Prioritized Execution Roadmap**: 
       * Outline a step-by-step technical implementation roadmap breaking down which services to tackle first, second, and third.

    Format the output elegantly in Markdown with clear columns or headers. Ensure code samples are a balanced part of the report alongside text summaries.
    """
    
    user_intent = tool_context.state.get("user_intent")
    if user_intent:
        prompt += f"\n\nCRITICAL: Align your strategy and recommendations with the following user goals and constraints:\n{user_intent}\n"
        
    result = await analyze_codebase_with_gemini(secure_temp_repo_dir, prompt)

    
    tool_context.state["cloud_strategy_analysis_result"] = result
    return True
