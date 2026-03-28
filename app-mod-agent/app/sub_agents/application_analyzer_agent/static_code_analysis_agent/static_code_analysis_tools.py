import os
import json
import logging
import subprocess
from google.adk.tools import ToolContext
from ..utils.gemini_utils import analyze_codebase_with_gemini

async def perform_static_code_analysis(tool_context: ToolContext) -> bool:
    """
    Analyzes the codebase and performs static code analysis.
    """
    secure_temp_repo_dir = tool_context.state.get("secure_temp_repo_dir")
    
    if not os.path.exists(secure_temp_repo_dir):
         logging.error("Static Code Analysis: Directory %s does not exist", secure_temp_repo_dir)
         return False
         
    files_to_scan = os.listdir(secure_temp_repo_dir)
    logging.info("Static Code Analysis found %d items to scan in directory.", len(files_to_scan))
    if len(files_to_scan) == 0:
        logging.warning("Static Code Analysis Staging directory is empty. Nothing to analyze.")

    prompt = """
    Perform a structural static code analysis on this application codebase.
    Avoid high-level or platitude responses. Provide concrete examples:
    1. **Code Smells & Anti-patterns**: Scan for Fat Controllers, overlapping interface responsibilities, N+1 query loops, or bloated utility files. Cite specific file names.
    2. **Categorized Breakdown**: Group findings comprehensively into High, Medium, and Info Severity tiers.
    3. **Structural Meaning**: Explain how modular or tightly-coupled the project is today structurally, describing how that hinders or encourages cloud modernization later.
    4. **Recommendations**: Highlight actionable line items providing code adjustments where applicable.

    Format the output elegantly in Markdown.
    """
    try:
        logging.info("Executing semgrep scan --config auto...")
        semgrep_result = subprocess.run(
            ["semgrep", "scan", "--config", "auto", "--json", "."],
            cwd=secure_temp_repo_dir,
            capture_output=True,
            text=True,
        )
        
        # Semgrep returns 0 if NO findings; returns 1 if findings ARE found. Both are "success" status for analysis.
        if semgrep_result.returncode in [0, 1]:
            if semgrep_result.stdout.strip():
                try:
                    json.loads(semgrep_result.stdout)
                    logging.debug("--- [Semgrep Raw Output] ---")
                    logging.debug(semgrep_result.stdout)
                    logging.debug("----------------------------")
                    prompt += f"I have run 'semgrep' to scan the codebase for security flaws and anti-patterns. Here is the JSON output:\n{semgrep_result.stdout}\n\nPlease factor these findings into your static code analysis report.\n"
                    logging.info("Semgrep findings attached successfully.")
                except json.JSONDecodeError:
                    logging.warning("Semgrep executed but stdout was not valid JSON.")
            else:
                logging.info("Semgrep executed successfully but returned empty output.")
        else:
            logging.warning("Semgrep execution error or crash. Exit Code: %d", semgrep_result.returncode)
            logging.warning("Semgrep Stderr: %s", semgrep_result.stderr)
            
    except Exception as e:
        logging.warning("Failed to run semgrep due to exception: %s", e)


    result = await analyze_codebase_with_gemini(secure_temp_repo_dir, prompt)

    
    tool_context.state["static_code_analysis_result"] = result
    return True
