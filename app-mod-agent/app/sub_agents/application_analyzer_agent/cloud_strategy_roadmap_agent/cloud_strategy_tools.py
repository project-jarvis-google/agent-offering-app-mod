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
    Analyze the cloud readiness, 12-Factor compliance, and structural modernization potential of this application based on the supplied codebase. 
    Do NOT provide generic guidance. You are a Lead Google Cloud Migration Architect. You MUST provide a concrete, exhaustive, and highly actionable Google Cloud modernization strategy and roadmap covering exactly the following dimensions in rigorous detail:

    1. **Migration Overview**: Provide a high-level executive summary of the recommended migration path, target cloud operating model, and expected operational efficiency outcomes.
    2. **Migration Targets in GCP (Core Workloads)**: 
       * For each primary legacy component (Compute, Database, Storage, Messaging), recommend the optimal managed GCP target (Cloud Run vs GKE vs App Engine).
       * Present a detailed Markdown table with columns: `| Legacy Component | Recommended GCP Service | R-Strategy (5 R's) | Justification (Pros & Cons Weigh-In) | Complexity (L/M/H) |`.
    3. **Additional Recommended Google Cloud Services (Ecosystem Integration)**: 
       * Identify and recommend supplementary GCP services that the architecture can benefit from (CI/CD with Cloud Build/Artifact Registry, Observability with Cloud Logging/Monitoring, Secret Management with Secret Manager, Object Storage with Cloud Storage, Async Messaging with Pub/Sub, Caching with Memorystore).
       * Present an exhaustive Markdown table with columns: `| Domain / Capability | Recommended GCP Service | Value Proposition & Relevance | Implementation Complexity (L/M/H) |`.
    4. **Zero-Downtime Database Migration Mechanics**: 
       * Outline the exact operational stages for a zero-downtime database cutover plan. Describe schema export validation, continuous Change Data Capture (CDC) replication setup via Google Cloud Database Migration Service (DMS), and staged read-replica elevation mechanics.
    5. **12-Factor App State Decoupling & Refactoring**: 
       * Perform an explicit audit of local in-memory caching layers (e.g., Caffeine, EhCache) and local filesystem access. Provide illustrative refactoring code diffs demonstrating exactly how to abstract localized state into Google Cloud Memorystore (Redis) and Google Cloud Storage.
       * Detail event-driven refactoring opportunities (e.g., introducing Pub/Sub message wrappers around synchronous batch operations).
    6. **Target Fit & Least-Privilege IAM Mapping**: 
       * Identify migration blockers (hardcoded absolute paths, tightly coupled localhost socket bindings) and provide remediation diffs.
       * Map out Workload Identity security requirements in a table with columns: `| Container Service / Component | Service Account Role Binding | Permissions Included | Target Bound GCP Resource |`. Detail specific IAM roles (e.g., roles/cloudsql.client, roles/secretmanager.secretAccessor).
       * Provide sample Kubernetes or Cloud Run service YAML diffs demonstrating correct environment variables and secret injection.
    7. **Prioritized Execution Roadmap (Strangler Fig Implementation)**: 
       * Outline a step-by-step technical implementation roadmap breaking down execution into Phased delivery sprints (Phase 1: Foundation & Replatform, Phase 2: Security & 12-Factor Modernization, Phase 3: Strangler Fig Microservice Decoupling).
       * For Phase 3, provide explicit API Gateway routing rules and strategies for isolating legacy bounded contexts into decoupled Cloud Run microservices.

    Format the output elegantly in Markdown with deep technical detail, structured tables, and illustrative diffs.
    """
    
    user_intent = tool_context.state.get("user_intent")
    if user_intent:
        prompt += f"\n\nCRITICAL: Align your strategy and recommendations with the following user goals and constraints:\n{user_intent}\n"
    else:
        tool_context.state["user_intent"] = "No specific user constraints or intent provided."
        
    result = await analyze_codebase_with_gemini(secure_temp_repo_dir, prompt)

    
    tool_context.state["cloud_strategy_analysis_result"] = result
    return True
