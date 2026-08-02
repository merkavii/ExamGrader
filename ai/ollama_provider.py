# * ==============================================================================
# *                       OllamaProvider (Implementation)
# * ==============================================================================
# ? پیاده‌سازی LLMClient با فراخوانی HTTP API محلی Ollama.
# ? مستندات API: POST {base_url}/api/generate با بدنه {"model", "prompt", "stream": false}

import requests

from ai.llm_client import LLMClient


class OllamaProvider(LLMClient):
    def __init__(self, model: str, base_url: str, timeout_seconds: int = 60) -> None:
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds

    def complete(self, prompt: str) -> str:
        response = requests.post(
            f"{self._base_url}/api/generate",
            json={"model": self._model, "prompt": prompt, "stream": False},
            timeout=self._timeout_seconds,
        )
        # ! اگر Ollama در دسترس نباشد یا مدل بارگذاری نشده باشد، این خط با
        # ! requests.exceptions.RequestException خطا می‌دهد. Grader صداکننده
        # ! باید این خطا را بگیرد و پاسخ را NEEDS_REVIEW علامت بزند، نه Crash کند.
        response.raise_for_status()
        return response.json()["response"]
