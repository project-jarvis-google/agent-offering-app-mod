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
    Analyze the cloud readiness and modernization potential of this application based on the supplied codebase. 
    Do NOT provide generic guidance. You MUST provide a concrete, exhaustive, and highly actionable Google Cloud modernization strategy and roadmap covering exactly the following dimensions:

    1. **Migration Overview**: Provide a high-level executive summary of the recommended migration path, target cloud operating model, and expected business outcomes.
    2. **Migration Targets in GCP (Core Workloads)**: 
       * For each primary legacy component (e.g., Compute, Database, Messaging), recommend the optimal GCP target (e.g., Cloud Run vs GKE vs App Engine).
       * Present a detailed Markdown table with columns: `| Legacy Component | Recommended GCP Service | R-Strategy (5 R's) | Justification (Pros & Cons Weigh-In) | Complexity (L/M/H) |`.
    3. **Additional Recommended Google Cloud Services (Ecosystem Integration)**: 
       * Identify and recommend supplementary GCP services that the customer's architecture can benefit from (e.g., CI/CD with Cloud Build/Artifact Registry, Observability with Cloud Logging/Monitoring, Secret Management with Secret Manager, Object Storage with Cloud Storage, Async Messaging with Pub/Sub, Caching with Memorystore).
       * Present an exhaustive Markdown table with columns: `| Domain / Capability | Recommended GCP Service | Value Proposition & Relevance | Implementation Complexity (L/M/H) |`.
    4. **Migration Dependencies & Pre-requisites**: 
       * Outline critical sequencing dependencies (e.g., establishing Cloud Interconnect/VPN, setting up IAM & Resource Hierarchy, completing Database Migration before application cutover).
    5. **Architectural Modernization Opportunities**: 
       * Detail concrete pointer-level refactoring and architectural modernization opportunities (e.g., decoupling state, adopting asynchronous event-driven patterns, breaking monoliths into microservices) to make the application cloud-native.
    6. **Migration Blockers & Remediation**: 
       * Call out hard-coded absolute paths, tightly coupled localhost bindings, or hardcoded IPs that will block containerization.
       * Provide illustrative code snippets demonstrating the issue and a suggested fix in standard markdown `diff` format.
    7. **Prioritized Execution Roadmap**: 
       * Outline a step-by-step technical implementation roadmap breaking down execution into Phased delivery plans.

    Format the output elegantly in Markdown with clear columns, tables, and headers. Ensure code samples are a balanced part of the report alongside text summaries.
    """
    
    user_intent = tool_context.state.get("user_intent")
    if user_intent:
        prompt += f"\n\nCRITICAL: Align your strategy and recommendations with the following user goals and constraints:\n{user_intent}\n"
    else:
        tool_context.state["user_intent"] = "No specific user constraints or intent provided."
        
    result = await analyze_codebase_with_gemini(secure_temp_repo_dir, prompt)

    
    tool_context.state["cloud_strategy_analysis_result"] = result
    return True
