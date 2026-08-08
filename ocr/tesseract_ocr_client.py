# * ==============================================================================
# *                    TesseractOCRClient (Implementation)
# * ==============================================================================
# ? پیاده‌سازی OCRClient با pytesseract/Tesseract محلی - بدون نیاز به سرویس
# ? ابری یا اتصال اینترنت (برخلاف OllamaProvider که به یک سرور محلی وصل
# ? می‌شود، Tesseract کاملاً in-process اجرا می‌شود).
#
# ! پیش‌نیاز محیطی: باینری tesseract باید نصب باشد + بسته زبان مربوطه
# ! (مثلاً tesseract-ocr-fas برای فارسی، از طریق apt). بدون بسته زبان، خروجی
# ! برای متن فارسی بی‌معنا خواهد بود - این محدودیت نصب سیستم است، نه باگ این کلاس.

import io

import pytesseract
from PIL import Image
from pytesseract import Output

from ocr.ocr_client import OCRClient, OCRLine, OCRResult


class TesseractOCRClient(OCRClient):
    def __init__(self, language: str = "fas+eng") -> None:
        # ? "fas+eng" یعنی Tesseract همزمان دو زبان را در نظر می‌گیرد - لازم
        # ? چون پاسخ‌های عددی و برخی نام‌ها ممکن است با ارقام/حروف انگلیسی
        # ? نوشته شده باشند.
        self._language = language

    def extract_text(self, image_bytes: bytes) -> OCRResult:
        image = Image.open(io.BytesIO(image_bytes))

        # ? image_to_data به‌جای image_to_string استفاده می‌شود چون هم مرز
        # ? خطوط (line_num/block_num/par_num) هم Confidence per-word را
        # ? می‌دهد - بدون آن نه می‌شد پاسخ‌ها را به سؤال‌ها نگاشت کرد، نه
        # ? Confidence واقعی per-answer داشتیم.
        data = pytesseract.image_to_data(
            image, lang=self._language, output_type=Output.DICT
        )

        lines = self._group_words_into_lines(data)
        overall_confidence = (
            sum(line.confidence for line in lines) / len(lines) if lines else 0
        )

        return OCRResult(lines=lines, overall_confidence=overall_confidence)

    @staticmethod
    def _group_words_into_lines(data: dict) -> list[OCRLine]:
        # ? کلمات هم‌خط را بر اساس کلید ترکیبی (block, paragraph, line) کنار
        # ? هم جمع می‌کند - همان ساختاری که Tesseract داخلی تشخیص می‌دهد.
        words_by_line: dict[tuple[int, int, int], list[tuple[str, int]]] = {}

        for word, conf, block, par, line in zip(
            data["text"], data["conf"], data["block_num"], data["par_num"], data["line_num"]
        ):
            if not word.strip() or int(conf) < 0:
                # ! conf=-1 یعنی این "کلمه" یک بلوک غیرمتنی است (مثلاً فاصله
                # ! خالی تشخیص‌داده‌شده) - نباید در متن یا میانگین حساب شود.
                continue
            key = (block, par, line)
            words_by_line.setdefault(key, []).append((word, int(conf)))

        result_lines = []
        for key in sorted(words_by_line.keys()):
            words = words_by_line[key]
            line_text = " ".join(w for w, _ in words)
            line_confidence = sum(c for _, c in words) / len(words)
            result_lines.append(OCRLine(text=line_text, confidence=line_confidence))

        return result_lines
