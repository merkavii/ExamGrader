# * ==============================================================================
# *                      FakeLLMClient (Test Double)
# * ==============================================================================
# ? این کلاس فقط برای تست است - جایگزین OllamaProvider واقعی می‌شود تا
# ? Grader ها بدون نیاز به سرور Ollama واقعی قابل تست باشند.

from ai.llm_client import LLMClient


class FakeLLMClient(LLMClient):
    def __init__(self, fixed_response: str) -> None:
        self._fixed_response = fixed_response
        self.last_prompt: str | None = None

    def complete(self, prompt: str) -> str:
        self.last_prompt = prompt
        return self._fixed_response


class RaisingLLMClient(LLMClient):
    """? برای شبیه‌سازی خرابی/timeout در ارتباط با مدل زبانی."""

    def complete(self, prompt: str) -> str:
        raise ConnectionError("Simulated LLM connection failure")
