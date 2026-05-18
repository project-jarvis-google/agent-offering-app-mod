import os
import json
import logging
import subprocess
from google.adk.tools import ToolContext
from ..utils.gemini_utils import analyze_codebase_with_gemini

async def perform_dependency_analysis(tool_context: ToolContext) -> bool:
    """
    Analyzes the codebase and generates dependency mapping.
    """
    secure_temp_repo_dir = tool_context.state.get("secure_temp_repo_dir")
    logging.info("Dependency Analysis trigger for secure_temp_repo_dir => %s", secure_temp_repo_dir)

    if not secure_temp_repo_dir or not os.path.exists(secure_temp_repo_dir):
        logging.error("Dependency Analysis: No codebase directory found in state or path invalid.")
        return False
        
    files_to_scan = os.listdir(secure_temp_repo_dir)
    logging.info("Dependency Analysis found %d items in temp directory to scan.", len(files_to_scan))
    if len(files_to_scan) == 0:
        logging.warning("Dependency Analysis Staging directory is empty. Nothing to analyze.")

    prompt = """Analyze the dependencies (e.g., pom.xml, package.json, requirements.txt, go.mod, etc.) and the complete Syft SBOM output found in the codebase.
Do NOT provide generic or high-level summaries. You MUST provide an exhaustive, highly detailed composition and dependency analysis covering:
1. **Domain-by-Domain Technology Stack Breakdown (For Section 2)**: Categorize all detected technologies, languages, frameworks, databases, and third-party libraries into distinct architectural domains (e.g., Backend Framework, Language & Runtime, Databases, Frontend, DevOps/Build Tools). For each domain, provide a clear Markdown table with EXACTLY the following columns:
| Technology/Tool Name | Version | Purpose/Role | EOL Status & Replacement Recommendation |
Ensure every entry specifies its exact version (or marks as Inherited/Managed), explains its specific purpose/role in the application, and provides a concrete End-of-Life (EOL) status assessment (e.g., 'Not EOL. Actively maintained.' or 'EOL/Deprecated. Upgrade recommended to X.').
2. **Complete Bill of Materials (BOM) Inventory (For Section 5)**: Present an exhaustive inventory of all detected packages, libraries, and dependencies across all build systems (`pom.xml`, `package.json`, `requirements.txt`, `go.mod`, `build.gradle`, etc.) and Syft SBOM scans.
3. **Problematic Library Risk Matrix & Recommendations**: Provide a comprehensive Markdown table mapping all problematic packages: `| Low-Level Package Name | Current Version | Detected Build Manifest | Vulnerability / Deprecation / License Risk | Actionable Remediation & Upgrade Target |`. Ensure you explicitly provide concrete upgrade recommendations for every outdated or risky library to give users full confidence.
4. **License Compliance Audit**: Identify restrictive copyleft licenses (GPL, AGPL) vs permissive licenses (MIT, Apache).
5. **Actionable Configuration Upgrade Diffs**: For critical dependency issues or recommended upgrades, provide concrete markdown `diff` blocks demonstrating exactly how to update configuration files to secure versions.

Format the output elegantly in Markdown, ensuring a good mix of text summary, structured tables, and code samples.\n\n"""
    try:
        logging.info("Executing syft scan dir:. -o json --override-default-catalogers all --enrich all...")
        syft_result = subprocess.run(
            ["syft", "scan", "dir:.", "-o", "json", "--override-default-catalogers", "all", "--enrich", "all"],
            cwd=secure_temp_repo_dir,
            capture_output=True,
            text=True,
            check=True
        )
        
        if syft_result.stdout.strip():
             try:
                 json.loads(syft_result.stdout)
                 logging.info("--- [Syft Raw Output] ---")
                 logging.info(syft_result.stdout)
                 logging.info("-------------------------")
                 prompt += f"I have run 'syft' to generate an SBOM configuration. Here is the JSON output:\n{syft_result.stdout}\n\nPlease factor this into your dependency analysis.\n"
                 logging.info("Syft findings attached successfully.")
             except json.JSONDecodeError:
                 logging.warning("Syft executed but stdout was not valid JSON.")
        else:
             logging.info("Syft executed successfully but returned empty output.")

    except subprocess.CalledProcessError as e:
        logging.warning("Failed to run syft. Exit Code: %d", e.returncode)
        logging.warning("Syft Stdout: %s", e.stdout)
        logging.warning("Syft Stderr: %s", e.stderr)
    except Exception as e:
        logging.warning("Failed to run syft due to exception: %s", e)


    result = await analyze_codebase_with_gemini(secure_temp_repo_dir, prompt)

    
    tool_context.state["dependency_analysis_result"] = result
    return True
