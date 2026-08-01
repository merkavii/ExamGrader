# * ==============================================================================
# *                         Number Normalizer
# * ==============================================================================
# ? معلم یا دانش‌آموز ممکن است عدد را با رقم فارسی (۹.۸۱) یا عربی (٩.٨١) تایپ کند.
# ? NumericGrader در فازهای بعدی فقط با float کار می‌کند، پس این تبدیل باید همین‌جا
# ? در لایه ورودی/نرمال‌سازی اتفاق بیفتد - نه داخل خود Grader.

_PERSIAN_DIGITS = "۰۱۲۳۴۵۶۷۸۹"
_ARABIC_DIGITS = "٠١٢٣٤٥٦٧٨٩"
_ASCII_DIGITS = "0123456789"

_DIGIT_TRANSLATION_TABLE = str.maketrans(
    _PERSIAN_DIGITS + _ARABIC_DIGITS,
    _ASCII_DIGITS + _ASCII_DIGITS,
)


def normalize_numeric_string(raw_value: str) -> str:
    """? ارقام فارسی/عربی داخل یک رشته را به ارقام انگلیسی تبدیل می‌کند."""
    return raw_value.translate(_DIGIT_TRANSLATION_TABLE)


def parse_number(raw_value: str) -> float:
    """
    ? رشته عددی (با ارقام فارسی/عربی/انگلیسی) را به float معتبر تبدیل می‌کند.

    ! اگر مقدار قابل تبدیل به عدد نباشد، ValueError صریح می‌دهد تا لایه
    ! input آن را به‌عنوان خطای اعتبارسنجی به معلم نشان دهد - نه این‌که
    ! بی‌صدا None برگرداند.
    """
    normalized = normalize_numeric_string(raw_value).strip()
    try:
        return float(normalized)
    except ValueError as error:
        raise ValueError(f"'{raw_value}' is not a valid number") from error
