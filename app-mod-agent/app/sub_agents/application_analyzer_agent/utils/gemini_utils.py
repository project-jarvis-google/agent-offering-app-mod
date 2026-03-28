import os
import logging
import asyncio
import subprocess

async def analyze_codebase_with_gemini(secure_temp_repo_dir: str, prompt: str, model_name: str = "gemini-3.1-pro-preview") -> str:
    """
    Analyzes the codebase directly using the gemini CLI which handles large codebases natively.
    """
    if not secure_temp_repo_dir or not os.path.exists(secure_temp_repo_dir):
        return "Error: Codebase directory not found."

    gemini_env = os.environ.copy()
    
    # Check if GEMINI_API_KEY is available
    if not os.getenv("GEMINI_API_KEY"):
        logging.warning("GEMINI_API_KEY is not set in environment. Analysis might fail.")
    else:
        gemini_env["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY")

    gemini_env["GEMINI_MODEL"] = model_name
    logging.info("Executing gemini CLI on %s with model %s...", secure_temp_repo_dir, model_name)

    try:
        # We use asyncio.create_subprocess_exec to avoid blocking the Event Loop
        process = await asyncio.create_subprocess_exec(
            "gemini",
            "--model", model_name,
            "-p", prompt,
            cwd=secure_temp_repo_dir,
            env=gemini_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=300)
        
        stdout_str = stdout.decode().strip()
        stderr_str = stderr.decode().strip()

        if process.returncode != 0:
            logging.error("Gemini CLI returned non-zero exited code %d. Stderr: %s", process.returncode, stderr_str)
            return f"Analysis Failed: {stderr_str}"
            
        return stdout_str
    except asyncio.TimeoutError:
         logging.error("Gemini CLI execution timed out after 300 seconds.")
         if process:
              process.kill()
         return "Analysis Failed: Gemini CLI timed out."
    except Exception as e:
         logging.error("Gemini CLI API Error: %s", e)
         if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
              return "Analysis Suspended: Continuous Quota Exhaustion (Rate Limit). Please check quota settings."
         return f"Analysis Failed: {str(e)}"

