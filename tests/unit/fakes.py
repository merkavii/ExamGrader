# * ==============================================================================
# *                      Test Doubles (Fakes)
# * ==============================================================================
# ? این فایل فقط برای تست است - جایگزین سرویس‌های خارجی واقعی (Ollama، Tesseract)
# ? می‌شود تا Grader ها و Extractor ها بدون نیاز به آن سرویس‌ها قابل تست باشند.

from ai.llm_client import LLMClient
from ocr.ocr_client import OCRClient, OCRLine, OCRResult


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


class FakeOCRClient(OCRClient):
    """? جایگزین TesseractOCRClient واقعی - بدون نیاز به باینری/بسته زبان نصب‌شده."""

    def __init__(self, lines: list[OCRLine]) -> None:
        self._lines = lines

    def extract_text(self, image_bytes: bytes) -> OCRResult:
        overall = (
            sum(line.confidence for line in self._lines) / len(self._lines)
            if self._lines
            else 0
        )
        return OCRResult(lines=self._lines, overall_confidence=overall)
