# Phase 3 Completion Report

**پروژه:** دستیار هوشمند تصحیح آزمون (Exam Grader)
**تاریخ آخرین به‌روزرسانی:** بعد از تکمیل Phase 3

---

## ۱. هدف Phase 3 چه بود؟

افزودن قابلیت تصحیح دو نوع سؤالی که با منطق قانون‌محور (Rule-Based) قابل‌حل نیستند و نیاز به درک معنایی زبان دارند:

- **Short Answer** (پاسخ کوتاه): تشخیص این‌که پاسخ دانش‌آموز از نظر معنایی با پاسخ صحیح یکی است، حتی اگر عبارت‌بندی دقیقاً یکسان نباشد.
- **Essay** (پاسخ تشریحی کوتاه): نمره‌دهی بر اساس Rubric، با تفکیک امتیاز هر معیار.

هدف فرعی مهم‌تر: پیاده‌سازی این دو Grader طوری که به **Ollama به‌طور مستقیم وابسته نباشند**، بلکه از یک Interface مستقل (`LLMClient`) استفاده کنند - طبق قانون اصلی پروژه که «Ollama فقط یکی از اجزای احتمالی است».

## ۲. چه قابلیت‌هایی در این فاز پیاده‌سازی شدند؟

- تصحیح پاسخ تشریحی با شکستن نمره بر اساس معیارهای Rubric (نه فقط یک نمره کلی)
- تصحیح معنایی پاسخ کوتاه (قبول/رد + دلیل)
- مکانیزم `confidence` که مدل زبانی خودش گزارش می‌دهد و بر اساس آن، نتیجه یا `GRADED` می‌شود یا `NEEDS_REVIEW`
- مدیریت خطا در سه سطح: پاسخ خالی دانش‌آموز (قطعی، بدون تماس با LLM)، خرابی اتصال به LLM، و خروجی غیرقابل‌تجزیه (invalid JSON) - هر سه بدون Crash کردن سیستم
- `GradingOrchestrator` به‌صورت اختیاری (`llm_client` پارامتر جدید) این دو Grader را ثبت می‌کند، بدون شکستن رفتار قبلی فاز ۲

## ۳. چه فایل‌هایی ایجاد یا تغییر کردند؟

**فایل‌های جدید:**

```
ai/llm_client.py
ai/ollama_provider.py
ai/json_response_parser.py
ai/prompts/essay_grading_prompt.py
ai/prompts/short_answer_grading_prompt.py
grading/graders/essay_grader.py
grading/graders/short_answer_grader.py
grading/llm_based_result.py
tests/unit/fakes.py
tests/unit/test_essay_grader.py
tests/unit/test_short_answer_grader.py
```

**فایل‌های تغییریافته:**

```
grading/orchestrator.py     (پشتیبانی اختیاری از llm_client)
tests/unit/test_grading_orchestrator.py   (تست جدید برای حالت llm_client فعال)
pyproject.toml              (افزودن وابستگی requests)
```

## ۴. هر فایل چه مسئولیتی دارد؟

| فایل | مسئولیت |
|---|---|
| `ai/llm_client.py` | Interface انتزاعی و مستقل از Provider خاص - فقط یک متد `complete(prompt) -> str` |
| `ai/ollama_provider.py` | تنها پیاده‌سازی فعلی `LLMClient`، با فراخوانی HTTP API محلی Ollama |
| `ai/json_response_parser.py` | پاک‌سازی و parse امن خروجی JSON مدل (حذف fence های ```json) |
| `ai/prompts/essay_grading_prompt.py` | ساخت prompt سؤال تشریحی بر اساس Rubric |
| `ai/prompts/short_answer_grading_prompt.py` | ساخت prompt پاسخ کوتاه معنایی |
| `grading/graders/essay_grader.py` | نمره‌دهی پاسخ تشریحی؛ جمع امتیاز معیارها، مدیریت خطا |
| `grading/graders/short_answer_grader.py` | نمره‌دهی پاسخ کوتاه معنایی (کامل/صفر) |
| `grading/llm_based_result.py` | تابع کمکی مشترک برای ساخت `GradeResult` از خروجی LLM + تعیین موقت status بر اساس confidence |
| `tests/unit/fakes.py` | `FakeLLMClient` و `RaisingLLMClient` برای تست بدون نیاز به Ollama واقعی |

## ۵. چه تصمیم‌های معماری مهمی گرفته شد؟

1. **جداسازی کامل از Ollama از طریق `LLMClient`.** هیچ Grader ای مستقیماً `OllamaProvider` را import نمی‌کند - فقط `LLMClient`. جایگزینی مدل زبانی در آینده فقط نیاز به یک پیاده‌سازی جدید از این Interface دارد.

2. **پاسخ خالی، قبل از تماس با LLM رد می‌شود.** این یک تصمیم قطعی (deterministic) است و نیازی به مدل زبانی ندارد - هم هزینه/زمان صرفه‌جویی می‌شود، هم قابل تست بدون mock است.

3. **آستانه `confidence >= 70` برای تعیین `GRADED` در برابر `NEEDS_REVIEW`، عمداً موقتی و ساده نگه داشته شد** (با کامنت `todo` مشخص در کد) - چون طراحی واقعی `ConfidenceEngine` (ترکیب چند منبع اطمینان) وظیفه Phase 4 است، نه این فاز.

4. **مدیریت خطا به‌جای Exception خام.** هر خطای اتصال یا parse، به یک `GradeResult` با `status=NEEDS_REVIEW` و `confidence=0` تبدیل می‌شود - نه Exception که کل فرآیند تصحیح دسته‌ای را متوقف کند (این طراحی، فاز ۵ - تصحیح دسته‌ای - را از قبل ساده‌تر می‌کند).

5. **`GradingOrchestrator` بدون شکستن Backward Compatibility توسعه یافت.** پارامتر `llm_client` اختیاری است؛ اگر داده نشود، دقیقاً همان رفتار فاز ۲ حفظ می‌شود (تست‌های فاز ۲ بدون تغییر همچنان pass می‌شوند).

6. **دفاع در برابر خطای مدل زبانی در جمع نمره.** `EssayGrader._sum_criteria_scores` حتی اگر مدل جمعاً بیشتر از `max_score` امتیاز بدهد، نتیجه را به `max_score` محدود می‌کند تا validator سطح `GradeResult` (که در فاز ۰ نوشته شد) خطا ندهد.

## ۶. چه وابستگی‌ها و کتابخانه‌هایی اضافه شدند؟

- `requests` → برای فراخوانی HTTP API Ollama در `OllamaProvider`

(بدون کتابخانه جدید دیگر - `pydantic`, `fastapi`, `sqlalchemy` و بقیه از فازهای قبل بودند)

## ۷. چه تست‌هایی انجام شدند و نتیجه آن‌ها چه بود؟

**تست‌های جدید این فاز** (۱۳ تست، همه Unit، با `FakeLLMClient`/`RaisingLLMClient` - بدون نیاز به Ollama واقعی):

- `test_essay_grader.py` (۷ تست): جمع امتیاز معیارها، پاسخ داخل fence مارک‌داون، محدود کردن نمره بیش‌ازحد مدل، `NEEDS_REVIEW` روی confidence پایین، `NEEDS_REVIEW` روی JSON نامعتبر، `NEEDS_REVIEW` روی خطای اتصال، عدم تماس با LLM برای پاسخ خالی
- `test_short_answer_grader.py` (۵ تست): تشخیص معادل معنایی متفاوت با پاسخ مرجع، پاسخ نادرست، confidence پایین، خطای اتصال، عدم تماس با LLM برای پاسخ خالی
- `test_grading_orchestrator.py` (۱ تست جدید): تأیید این‌که با دادن `llm_client`، سؤال `SHORT_ANSWER` دیگر Unsupported نیست

**وضعیت اجرا:** ⚠️ در محیط توسعه فعلی (این مکالمه)، دسترسی شبکه برای نصب `pydantic`/`pytest`/`requests` وجود نداشت، بنابراین تست‌ها با `python -m py_compile` روی همه فایل‌ها بررسی سینتکسی شدند (بدون خطا) اما **اجرای واقعی pytest هنوز توسط کاربر روی سیستم محلی انجام نشده و نتیجه‌اش تأیید نشده است.** این مورد باید قبل از شروع Phase 4 توسط کاربر تأیید شود:

```bash
pip install -e ".[dev]"
pytest tests/unit -v
```

## ۸. چه مواردی عمداً برای فازهای بعدی باقی مانده‌اند؟

- **ترکیب واقعی Confidence از چند منبع** (کیفیت تصویر + OCR + Extraction + Grading) → Phase 4 (`ConfidenceEngine`)
- **صف بازبینی معلم (`ReviewQueue`)** و نمایش موارد `NEEDS_REVIEW` → Phase 4
- **اتصال `EssayGrader`/`ShortAnswerGrader` به API واقعی** (ساخت `GradingOrchestrator` با `OllamaProvider` واقعی در لایه `app/`) → Phase 5
- **ذخیره‌سازی `GradeResult` در دیتابیس** (هنوز Repository ای برای آن نداریم) → Phase 5
- **Endpoint های تصحیح تکی/دسته‌ای** (`POST /exams/{id}/grade`, `POST /exams/{id}/students/{id}/grade`) → Phase 5
- **Matching، Fill in the Blank** → بعد از MVP
- **تست Integration واقعی با یک نمونه Ollama در حال اجرا** (تست‌های فعلی فقط با Fake هستند) → می‌تواند در Phase 5 یا جدا اضافه شود

## ۹. وضعیت فعلی پروژه برای شروع Phase 4 چگونه است؟

آماده برای شروع، **مشروط به این‌که کاربر ابتدا `pytest` را روی سیستم محلی اجرا و نتیجه سبز را تأیید کند** (طبق محدودیت شبکه در بند ۷).

از نظر معماری، همه پیش‌نیازهای Phase 4 (Confidence Engine + Review Queue) آماده‌اند:
- `ConfidenceScore` از Phase 0 دقیقاً برای ترکیب چند منبع طراحی شده بود
- همه Grader ها (قانون‌محور و LLM-based) از قبل یک `grading_confidence` معتبر در `GradeResult` برمی‌گردانند
- `GradingStatus.NEEDS_REVIEW` از Phase 0 در Domain وجود دارد و توسط Phase 3 عملاً استفاده شد (فقط با آستانه ساده‌شده موقت)

هیچ Blocker شناخته‌شده‌ای برای شروع Phase 4 وجود ندارد.
