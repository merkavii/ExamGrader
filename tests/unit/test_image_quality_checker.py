# * ==============================================================================
# *                    Tests: ImageQualityChecker
# * ==============================================================================
# ? این تست‌ها با تصاویر واقعی ساخته‌شده توسط NumPy/OpenCV اجرا می‌شوند - نه Mock -
# ? چون OpenCV در محیط توسعه واقعاً نصب است و منطق پردازش تصویر قابل اجرای واقعی است.

import numpy as np
import pytest

from extraction.image_quality.quality_checker import ImageQualityChecker


@pytest.fixture()
def checker() -> ImageQualityChecker:
    return ImageQualityChecker()


def test_sharp_high_contrast_image_is_acceptable(checker):
    # ? پس‌زمینه خاکستری روشن (شبیه کاغذ) با خطوط تیره کم‌تراکم برای لبه‌های
    # ! واضح - مقادیر زیر واقعاً اجرا و تأیید شده‌اند: هم واریانس Laplacian
    # ! بالای آستانه است (تیز)، هم میانگین روشنایی داخل بازه مجاز [40, 230].
    image = np.full((200, 200), 200, dtype=np.uint8)
    image[::30, :] = 60
    image[:, ::30] = 60

    report = checker.check(image)

    assert report.is_acceptable is True
    assert report.quality_score == 100.0
    assert report.issues == []


def test_uniform_blurry_image_is_flagged():
    # ? تصویر کاملاً یکنواخت (بدون هیچ لبه‌ای) => واریانس Laplacian صفر => تار
    checker = ImageQualityChecker()
    image = np.full((200, 200), 128, dtype=np.uint8)

    report = checker.check(image)

    assert report.is_acceptable is False
    assert "تار" in report.issues[0]
    assert report.quality_score < 100.0


def test_very_dark_image_is_flagged(checker):
    image = np.full((200, 200), 5, dtype=np.uint8)
    report = checker.check(image)
    assert any("تاریک" in issue for issue in report.issues)


def test_very_bright_image_is_flagged(checker):
    image = np.full((200, 200), 250, dtype=np.uint8)
    report = checker.check(image)
    assert any("نور" in issue for issue in report.issues)


def test_accepts_bgr_color_image_not_only_grayscale(checker):
    # ! ورودی رنگی (BGR سه‌کاناله) هم باید بدون خطا کار کند - تبدیل داخلی به
    # ! grayscale باید خودکار انجام شود. همان مقادیر تأییدشده تست بالا.
    color_image = np.full((200, 200, 3), 200, dtype=np.uint8)
    color_image[::30, :, :] = 60
    color_image[:, ::30, :] = 60

    report = checker.check(color_image)
    assert report.quality_score == 100.0
