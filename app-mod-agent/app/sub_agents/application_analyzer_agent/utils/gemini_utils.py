import os
import logging
from .base_analyzer import CodebaseAnalyzer
from .cli_analyzer import GeminiCliAnalyzer
from .gitingest_analyzer import GitingestAnalyzer

def get_analyzer() -> CodebaseAnalyzer:
    """
    Factory function to get the configured codebase analyzer.
    """
    method = os.getenv("CODE_ANALYSIS_METHOD", "gemini_cli").lower()
    if method == "gitingest":
        logging.info("Using Gitingest codebase analyzer.")
        return GitingestAnalyzer()
    else:
        logging.info("Using Gemini CLI codebase analyzer.")
        return GeminiCliAnalyzer()

async def analyze_codebase_with_gemini(secure_temp_repo_dir: str, prompt: str, model_name: str = "gemini-3.1-pro-preview") -> str:
    """
    Wrapper function that delegates to the configured analyzer.
    Existing tools call this function, so its signature remains unchanged.
    """
    analyzer = get_analyzer()
    return await analyzer.analyze(secure_temp_repo_dir, prompt, model_name)
