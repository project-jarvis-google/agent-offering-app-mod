from abc import ABC, abstractmethod

class CodebaseAnalyzer(ABC):
    @abstractmethod
    async def analyze(self, secure_temp_repo_dir: str, prompt: str, model_name: str) -> str:
        """
        Analyzes the codebase in secure_temp_repo_dir using the provided prompt and model.
        """
        pass
