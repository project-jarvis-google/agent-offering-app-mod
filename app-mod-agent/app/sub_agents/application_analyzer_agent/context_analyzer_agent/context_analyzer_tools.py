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
       * **Application Summary**: Provide a thorough, comprehensive business overview explaining what the application is, its primary operational domain, and the core problems it solves.
       * **Core Features & Capabilities**: Detail the primary business capabilities, main operational workflows, and domain boundaries established in the code.
       * **Primary Users & Personas**: Identify key user personas, client interfaces, upstream services, and external consumers interacting with the application. Detail the specific value proposition for each.
    2. **Frameworks & Core Libraries**: Identify major application frameworks, runtimes, and core architectural dependencies. Detail their exact structural roles, modular dependencies, and configuration management models.
    3. **Databases & Persistence Models**: Detect database drivers, ORMs, connection lifecycle pools, caching tiers, and raw filesystem access. Describe data flow models, transaction lifecycles, and state persistence contracts.
    4. **Utilities & Async Infrastructure**: Evaluate messaging brokers, background processing queues, scheduled worker daemons, and system utilities. Detail configuration injection patterns across environments.
    5. **Architectural Correlation & Data Flow**: Correlate technical components against directory structures and API contracts. Map exactly how modular services communicate and trace data across systemic boundaries.

    Format the output with professional executive rigor and deep technical detail in Markdown.
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

    tool_context.state["tokei_analysis_result"] = "No Tokei metrics captured."
    try:
        logging.info("Executing tokei analyzer over directory %s...", secure_temp_repo_dir)
        tokei_res = subprocess.run(
            ["tokei", ".", "--sort", "files"],
            cwd=secure_temp_repo_dir,
            capture_output=True,
            text=True,
            check=True
        )
        tokei_summary = tokei_res.stdout.strip()
        logging.info("Tokei execution successful. Output size: %d bytes", len(tokei_summary))
        logging.info("--- [Tokei Language Summary] ---\n%s\n-------------------------------", tokei_summary)
        
        tool_context.state["tokei_analysis_result"] = tokei_summary

    except subprocess.CalledProcessError as e:
        logging.warning("Failed to run tokei. Exit code: %d, Stderr: %s", e.returncode, e.stderr)
    except Exception as e:
        logging.warning("Failed to run tokei due to exception: %s", e)

    result = await analyze_codebase_with_gemini(secure_temp_repo_dir, prompt)
    
    tool_context.state["context_analysis_result"] = result
    return True

