import os
import logging
import subprocess
from google.adk.tools import ToolContext
from ..utils.gemini_utils import analyze_codebase_with_gemini


async def perform_context_analysis(tool_context: ToolContext) -> bool:
    """
    Analyzes the codebase and generates the context of the application.
    """
    secure_temp_repo_dir = tool_context.state.get("secure_temp_repo_dir")
    logging.info("Context Analysis trigger for secure_temp_repo_dir => %s", secure_temp_repo_dir)

    if not secure_temp_repo_dir or not os.path.exists(secure_temp_repo_dir):
        logging.error("No codebase directory found in state or directory path invalid.")
        return False
        
    files_to_scan = os.listdir(secure_temp_repo_dir)
    logging.info("Found %d items in temp directory to scan.", len(files_to_scan))
    if len(files_to_scan) == 0:
        logging.warning("The temporary staging directory is empty. Nothing to analyze.")
        
    prompt = """
    Analyze the architecture, business context, and purpose of this application based on the codebase provided. 
    Do NOT provide generic or high-level guidance. You MUST provide an exhaustive, deep-dive architectural and business analysis addressing the following:
    1. **Executive Business Context**:
       * **Application Summary**: Provide a concise summary (up to 5-6 lines max) explaining what the application is, its primary domain, and what it accomplishes based on codebase understanding.
       * **Core Features & Capabilities**: Identify the primary business capabilities, core features, and main workflows implemented in the code.
       * **Primary Users & Personas**: Infer the key user personas, upstream systems, or API consumers interacting with the application. Highlight the specific value and capabilities each persona derives from the system.
    2. **Frameworks & Core Libraries**: Identify major application frameworks (e.g., Spring Boot, FastAPI, React) and heavy-weight dependencies influencing the design. Detail their exact structural roles and configuration mechanisms.
    3. **Databases & Persistence**: Detect database drivers, ORMs, connection pools, caching layers, and local disk IO. Describe data flow models, connection lifecycles, and persistence strategies.
    4. **Utilities & Infrastructure**: Call out messaging queues, background worker threads, and system utilities. Explain configuration patterns and environmental requirements.
    5. **Architectural Correlation & Component Interactions**: explicitly correlate these technical components against the directory layout and modular boundaries. Describe precisely how separate modules and services communicate and function together systemically.

    Format the output elegantly in Markdown with comprehensive detail.
    """
    try:
        output_file = os.path.abspath(os.path.join(secure_temp_repo_dir, "stack.json"))
        logging.info("Executing @specfy/stack-analyser. Output target => %s", output_file)

        specfy_result = subprocess.run(
            ["npx", "--yes", "@specfy/stack-analyser", ".", "--output=stack.json"],
            cwd=secure_temp_repo_dir,
            capture_output=True,
            text=True,
            check=True
        )

        
        logging.info("Specfy run succeeded. Validated files in directory.")
        if os.path.exists(output_file):
            with open(output_file, 'r', encoding='utf-8') as f:
                stack_json = f.read()
            logging.info("--- [Specfy Raw Output] ---")
            logging.info(stack_json)
            logging.info("---------------------------")
            prompt += f"I have run '@specfy/stack-analyser' to detect the tech stack, components and SaaS layout. Here is the JSON structure:\n{stack_json}\n\nPlease factor this into your architecture and context analysis to give precise ecosystem breakdowns.\n"
            os.remove(output_file)
        else:
            logging.error("Specfy reported success, but output_file %s was not found.", output_file)

    except subprocess.CalledProcessError as e:
        logging.warning("Failed to run @specfy/stack-analyser. Exit Code: %d", e.returncode)
        logging.warning("Specfy Stdout: %s", e.stdout)
        logging.warning("Specfy Stderr: %s", e.stderr)
    except Exception as e:
        logging.warning("Failed to run @specfy/stack-analyser due to unexpected exception: %s", e)

    except Exception as e:
        logging.warning("Failed to run @specfy/stack-analyser due to exception: %s", e)

    result = await analyze_codebase_with_gemini(secure_temp_repo_dir, prompt)
    
    tool_context.state["context_analysis_result"] = result
    return True

