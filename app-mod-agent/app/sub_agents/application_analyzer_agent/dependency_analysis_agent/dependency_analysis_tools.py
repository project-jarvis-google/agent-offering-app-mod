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

    prompt = "Analyze the dependencies (e.g., pom.xml, package.json, requirements.txt, go.mod, etc.) found in the codebase. Identify key components, third-party libraries, and their relationships. For critical dependency issues or recommended upgrades, provide example diffs of the configuration files showing the changes in standard markdown `diff` format. Format the output in Markdown, ensuring a good mix of text summary and code samples.\n\n"
    try:
        logging.info("Executing syft dir:. -o json...")
        syft_result = subprocess.run(
            ["syft", "dir:.", "-o", "json"],
            cwd=secure_temp_repo_dir,
            capture_output=True,
            text=True,
            check=True
        )
        
        if syft_result.stdout.strip():
             try:
                 json.loads(syft_result.stdout)
                 logging.debug("--- [Syft Raw Output] ---")
                 logging.debug(syft_result.stdout)
                 logging.debug("-------------------------")
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
