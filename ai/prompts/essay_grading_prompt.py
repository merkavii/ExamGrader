# * ==============================================================================
# *                     Essay Grading Prompt Builder
# * ==============================================================================
# ? این تابع Prompt ای می‌سازد که از مدل می‌خواهد دقیقاً یک JSON با ساختار
# ? مشخص برگرداند - نه متن آزاد - تا EssayGrader بتواند آن را parse کند.

from domain.models.rubric import Rubric


def build_essay_grading_prompt(
    question_text: str,
    reference_answer: str,
    rubric: Rubric,
    student_answer: str,
) -> str:
    criteria_lines = "\n".join(
        f'- "{criterion.description}" (حداکثر امتیاز: {criterion.points})'
        for criterion in rubric.criteria
    )

    # ! دستور صریح "فقط JSON برگردان" حیاتی است - بدون آن مدل معمولاً توضیح
    # ! اضافه قبل/بعد JSON می‌نویسد که parse را می‌شکند.
    return f"""تو یک دستیار تصحیح آزمون هستی. باید پاسخ تشریحی یک دانش‌آموز را بر اساس
معیار نمره‌دهی (Rubric) زیر ارزیابی کنی.

سؤال:
{question_text}

پاسخ مرجع (نمونه):
{reference_answer}

معیارهای نمره‌دهی (Rubric):
{criteria_lines}

پاسخ دانش‌آموز:
{student_answer}

برای هر معیار Rubric، بررسی کن آیا پاسخ دانش‌آموز به آن اشاره کرده یا نه و امتیاز
متناسب (بین صفر تا حداکثر امتیاز آن معیار) بده. سپس یک عدد confidence بین ۰ تا ۱۰۰
بده که نشان می‌دهد چقدر به ارزیابی خودت مطمئن هستی (اگر پاسخ مبهم یا ناقص بود،
confidence را پایین بده).

فقط و فقط یک JSON با دقیقاً این ساختار برگردان، بدون هیچ متن اضافه قبل یا بعد آن:

{{
  "criteria_scores": [
    {{"description": "متن دقیق معیار", "points_awarded": عدد}}
  ],
  "reasoning": "توضیح کوتاه فارسی درباره دلیل امتیازها",
  "confidence": عدد بین ۰ تا ۱۰۰
}}"""
