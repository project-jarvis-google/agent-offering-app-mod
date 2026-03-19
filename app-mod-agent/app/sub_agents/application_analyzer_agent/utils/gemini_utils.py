import os
import logging
import asyncio
import random
from gitingest import ingest_async
from google import genai
from google.genai.errors import ClientError
from tenacity import retry, stop_after_attempt, wait_random_exponential, retry_if_exception

# Helper to retry on 429 inside ClientError
def is_rate_limit_error(e: Exception) -> bool:
    return isinstance(e, ClientError) and ("429" in str(e) or "RESOURCE_EXHAUSTED" in str(e))

@retry(
    retry=retry_if_exception(is_rate_limit_error),
    stop=stop_after_attempt(3),
    wait=wait_random_exponential(multiplier=2, max=30),
)
async def generate_content_with_retry(client, model, contents):
    """
    Wraps the call in tenacity back-off triggers specifically catching rate limits.
    """
    return await client.aio.models.generate_content(
        model=model,
        contents=contents,
    )

async def load_codebase_text(secure_temp_repo_dir: str) -> str:
    """
    Reads the codebase using Gitingest with size-limits, falling back to 
    standard traversal if ingest_async fails.
    """
    try:
        logging.info("Executing gitingest_async on %s", secure_temp_repo_dir)
        summary, tree, content = await ingest_async(
            secure_temp_repo_dir,
            max_file_size=200_000, 
            exclude_patterns={
                ".git/", "node_modules/", "venv/", "__pycache__/", 
                "dist/", "build/", "target/", ".idea/", ".vscode/",
                "*.pdf", "*.jar", "*.class", "*.pyc", "*.png", "*.jpg", 
                "*.zip", "*.tar.gz", "*.pkl", "*.db", "*.sqlite", "*.exe", "*.dll"
            }
        )
        full_codebase_text = f"### 📂 Directory Tree\n```text\n{tree}\n```\n\n### 📝 Code Contents\n{content}"
        logging.info("Gitingest serialization succeeded.")
        return full_codebase_text
    except Exception as e:
        logging.warning("Gitingest failed: %s. Falling back to basic traversal.", e)
        codebase_content = []
        MAX_FILE_SIZE = 100_000  # 100KB guardrail to avoid crashing memory or context window
        
        for root, dirs, files in os.walk(secure_temp_repo_dir):
            dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', 'venv', '__pycache__', '.idea', '.vscode', 'dist', 'build', 'target']]
            for file in files:
                if file.endswith(('.jar', '.class', '.pyc', '.png', '.jpg', '.pdf', '.zip', '.tar.gz', '.pkl', '.db', '.sqlite', '.exe', '.dll')):
                    continue
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, secure_temp_repo_dir)
                try:
                    if os.path.getsize(file_path) > MAX_FILE_SIZE:
                        continue
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        codebase_content.append(f"--- File: {relative_path} ---\n{content}\n")
                except Exception:
                    pass
        return "\n".join(codebase_content)

async def analyze_codebase_with_gemini(secure_temp_repo_dir: str, prompt: str, full_codebase_text: str = None) -> str:
    """
    Reads the codebase, packs it into a prompt, and calls Gemini natively
    using the google-genai SDK using async.
    """
    if not full_codebase_text:
        if not secure_temp_repo_dir or not os.path.exists(secure_temp_repo_dir):
            return "Error: Codebase directory not found."
        full_codebase_text = await load_codebase_text(secure_temp_repo_dir)
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key) if api_key else genai.Client()
    
    model_name = "gemini-2.5-pro"
    final_prompt = f"{prompt}\n\nHere is the codebase:\n{full_codebase_text}"
    
    # Stagger Execution Statically to break spike concurrent RPM collisions
    await asyncio.sleep(random.uniform(1.0, 4.0))

    try:
        response = await generate_content_with_retry(
            client=client,
            model=model_name,
            contents=final_prompt,
        )
        return response.text
    except Exception as e:
        logging.error("Gemini API Error after retries: %s", e)
        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
             return "Analysis Suspended: Continuous Quota Exhaustion (Rate Limit). Please check quota settings."
        return f"Analysis Failed: {str(e)}"


