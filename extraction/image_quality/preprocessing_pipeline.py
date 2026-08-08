# * ==============================================================================
# *                          ImagePreprocessor
# * ==============================================================================
# ? Pipeline پیش‌پردازش طبق طرح اولیه پروژه:
# ?   Raw Image -> Grayscale -> Deskew -> Perspective Correction ->
# ?   Denoise -> Contrast Adjustment -> (خروجی برای OCR)
#
# ! طبق همان طرح: "تصویر اصلی همیشه باید حفظ شود" و "Super Resolution نباید
# ! اطلاعات جدید و ساختگی تولید کند" - این پیاده‌سازی عمداً هیچ مرحله
# ! Super Resolution/تولید محتوا ندارد؛ فقط تبدیل‌های هندسی/نوری غیرمخرب.

import cv2
import numpy as np


class ImagePreprocessor:
    def process(self, image: np.ndarray) -> np.ndarray:
        """? ورودی: تصویر خام BGR. خروجی: تصویر آماده OCR (grayscale)."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        perspective_corrected = self._correct_perspective(gray)
        deskewed = self._deskew(perspective_corrected)
        denoised = cv2.fastNlMeansDenoising(deskewed, h=10)
        contrast_enhanced = self._enhance_contrast(denoised)
        return contrast_enhanced

    @staticmethod
    def _correct_perspective(gray_image: np.ndarray) -> np.ndarray:
        """
        ? تلاش می‌کند بزرگ‌ترین کانتور چهارگوشه (فرض: لبه برگه) را پیدا کند و
        ? حالت ذوزنقه‌ای ناشی از زاویه گرفتن عکس را به مستطیل صاف تبدیل کند.

        ! این یک روش best-effort است، نه تضمینی: اگر لبه برگه به‌وضوح در
        ! تصویر مشخص نباشد (مثلاً پس‌زمینه شلوغ یا برگه کل کادر را پر کرده)،
        ! هیچ کانتور مناسبی پیدا نمی‌شود و تصویر بدون تغییر برمی‌گردد - بهتر
        ! از این‌که با حدس اشتباه، تصویر را بدتر کنیم.
        """
        blurred = cv2.GaussianBlur(gray_image, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return gray_image

        largest_contour = max(contours, key=cv2.contourArea)
        image_area = gray_image.shape[0] * gray_image.shape[1]
        # ! کانتوری که خیلی کوچک است، احتمالاً برگه نیست - رد می‌شود تا یک
        # ! ناحیه کوچک تصادفی به‌جای کل برگه warp نشود.
        if cv2.contourArea(largest_contour) < image_area * 0.2:
            return gray_image

        perimeter = cv2.arcLength(largest_contour, True)
        approx = cv2.approxPolyDP(largest_contour, 0.02 * perimeter, True)
        if len(approx) != 4:
            return gray_image  # ? چهارگوشه واضحی پیدا نشد - رد می‌شویم، نه حدس

        corners = _order_corners(approx.reshape(4, 2).astype("float32"))
        width, height = _target_dimensions(corners)
        destination = np.array(
            [[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]],
            dtype="float32",
        )
        transform_matrix = cv2.getPerspectiveTransform(corners, destination)
        return cv2.warpPerspective(gray_image, transform_matrix, (width, height))

    @staticmethod
    def _deskew(gray_image: np.ndarray) -> np.ndarray:
        """
        ? زاویه کجی متن را با minAreaRect روی پیکسل‌های غیرسفید تخمین می‌زند
        ? و تصویر را چرخش می‌دهد تا صاف شود.

        ! اگر تصویر عملاً خالی/همه‌سفید باشد (هیچ پیکسل متنی برای تحلیل)،
        ! همان تصویر ورودی بدون تغییر برگردانده می‌شود - نه یک چرخش تصادفی.
        """
        binary = cv2.threshold(gray_image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
        coordinates = cv2.findNonZero(binary)
        if coordinates is None:
            return gray_image

        angle = cv2.minAreaRect(coordinates)[-1]
        # ? minAreaRect زاویه را بین -۹۰ تا ۰ برمی‌گرداند - تبدیل به بازه قابل‌فهم
        angle = -(90 + angle) if angle < -45 else -angle

        # ! اگر زاویه خیلی کوچک است (کمتر از نیم درجه)، چرخش نمی‌زنیم - چرخش
        # ! برای زاویه‌های ناچیز فقط نویز اضافه می‌کند، نه بهبود واقعی.
        if abs(angle) < 0.5:
            return gray_image

        height, width = gray_image.shape
        center = (width // 2, height // 2)
        rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        return cv2.warpAffine(
            gray_image,
            rotation_matrix,
            (width, height),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE,
        )

    @staticmethod
    def _enhance_contrast(gray_image: np.ndarray) -> np.ndarray:
        # ? CLAHE (Contrast Limited Adaptive Histogram Equalization) - بهبود
        # ? کنتراست موضعی، مناسب برای عکس‌هایی که بخشی از صفحه سایه دارد.
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        return clahe.apply(gray_image)


def _order_corners(points: np.ndarray) -> np.ndarray:
    """? چهار نقطه را به ترتیب ثابت (بالا-چپ، بالا-راست، پایین-راست، پایین-چپ) مرتب می‌کند."""
    ordered = np.zeros((4, 2), dtype="float32")
    coordinate_sum = points.sum(axis=1)
    ordered[0] = points[np.argmin(coordinate_sum)]  # بالا-چپ: کمترین x+y
    ordered[2] = points[np.argmax(coordinate_sum)]  # پایین-راست: بیشترین x+y
    coordinate_diff = np.diff(points, axis=1)
    ordered[1] = points[np.argmin(coordinate_diff)]  # بالا-راست: کمترین y-x
    ordered[3] = points[np.argmax(coordinate_diff)]  # پایین-چپ: بیشترین y-x
    return ordered


def _target_dimensions(corners: np.ndarray) -> tuple[int, int]:
    """? عرض/ارتفاع مستطیل مقصد را از فاصله واقعی گوشه‌های تشخیص‌داده‌شده محاسبه می‌کند."""
    (top_left, top_right, bottom_right, bottom_left) = corners
    width = max(
        int(np.linalg.norm(top_right - top_left)),
        int(np.linalg.norm(bottom_right - bottom_left)),
    )
    height = max(
        int(np.linalg.norm(bottom_left - top_left)),
        int(np.linalg.norm(bottom_right - top_right)),
    )
    return max(width, 1), max(height, 1)
