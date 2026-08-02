# * ==============================================================================
# *                      JSON Response Parser (Helper)
# * ==============================================================================
# ? مدل‌های زبانی گاهی خروجی JSON را داخل ```json ... ``` می‌پیچند یا قبل/بعدش
# ? متن اضافه می‌گذارند. این تابع این موارد رایج را پاک می‌کند قبل از json.loads.
#
# ! این تابع "بخشش‌گر" (lenient) است، نه اعتبارسنج. اگر بعد از پاک‌سازی هم
# ! JSON نامعتبر بود، ValueError می‌دهد - Grader صداکننده مسئول تصمیم درباره
# ! NEEDS_REVIEW است، نه این تابع.

import json
import re


def parse_json_response(raw_response: str) -> dict:
    cleaned = raw_response.strip()

    # ? حذف fence های ```json ... ``` یا ``` ... ``` در صورت وجود
    fence_match = re.match(r"^```(?:json)?\s*(.*?)\s*```$", cleaned, re.DOTALL)
    if fence_match:
        cleaned = fence_match.group(1)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as error:
        raise ValueError(f"LLM response is not valid JSON: {raw_response[:200]}") from error
