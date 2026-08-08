# * ==============================================================================
# *                          ImageQualityChecker
# * ==============================================================================
# ? قبل از صرف زمان/منابع روی OCR، کیفیت تصویر بررسی می‌شود. طبق طرح اولیه
# ? پروژه: "اگر کیفیت تصویر خیلی پایین باشد، سیستم باید بتواند درخواست عکس
# ? جدید بدهد و نباید با اطمینان کاذب نمره ثبت کند."

import cv2
import numpy as np
from pydantic import BaseModel

# ? آستانه‌های زیر با آزمایش دستی روی چند نمونه تصویر معمولی تنظیم شده‌اند؛
# ? اگر در عمل مقادیر کاذب زیاد دیدی (تصاویر خوب رد می‌شوند یا برعکس)، این
# ? دو عدد نقطه اول برای تنظیم دوباره هستند - بقیه Pipeline به آن‌ها وابسته نیست.
BLUR_THRESHOLD = 100.0  # ? واریانس Laplacian کمتر از این یعنی تصویر تار است
MIN_BRIGHTNESS = 40.0  # ? میانگین روشنایی (۰-۲۵۵) کمتر از این یعنی تصویر خیلی تاریک است
MAX_BRIGHTNESS = 230.0  # ? بیشتر از این یعنی نور بیش‌ازحد/سوخته


class ImageQualityReport(BaseModel):
    """? نتیجه بررسی کیفیت - is_acceptable تصمیم می‌گیرد ادامه Pipeline ارزش دارد یا نه."""

    quality_score: float  # ? ۰ تا ۱۰۰ - ورودی به ConfidenceEngine به‌عنوان image_quality
    is_acceptable: bool
    issues: list[str]


class ImageQualityChecker:
    def check(self, image: np.ndarray) -> ImageQualityReport:
        """? image باید یک آرایه OpenCV (BGR یا Grayscale) باشد."""
        gray = image if len(image.shape) == 2 else cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        issues: list[str] = []

        blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
        if blur_score < BLUR_THRESHOLD:
            issues.append("تصویر تار به نظر می‌رسد")

        brightness = float(np.mean(gray))
        if brightness < MIN_BRIGHTNESS:
            issues.append("تصویر خیلی تاریک است")
        elif brightness > MAX_BRIGHTNESS:
            issues.append("نور تصویر بیش‌ازحد زیاد است")

        # ? ترکیب ساده و شفاف دو سنجه به یک امتیاز ۰-۱۰۰ - هرکدام از دو مسئله
        # ? بالا نیمی از امتیاز را کم می‌کند؛ عمداً از فرمول پیچیده پرهیز شده.
        quality_score = 100.0
        if blur_score < BLUR_THRESHOLD:
            quality_score -= 50
        if brightness < MIN_BRIGHTNESS or brightness > MAX_BRIGHTNESS:
            quality_score -= 50
        quality_score = max(quality_score, 0.0)

        return ImageQualityReport(
            quality_score=quality_score,
            is_acceptable=len(issues) == 0,
            issues=issues,
        )
