# Phase 4 Completion Report

**پروژه:** دستیار هوشمند تصحیح آزمون (Exam Grader)
**تاریخ آخرین به‌روزرسانی:** بعد از تکمیل Phase 4

---

## ۱. هدف Phase 4 چه بود؟

طراحی و پیاده‌سازی دو مؤلفه:
- **ConfidenceEngine**: ترکیب چند منبع اطمینان (کیفیت تصویر، اطمینان Extraction، اطمینان Grader) به یک `final_score` واحد و تعیین این‌که نتیجه باید خودکار پذیرفته شود یا نیاز به بازبینی معلم دارد.
- **ReviewQueue**: مدیریت لیست نتایج نیازمند بازبینی و اعمال تصمیم نهایی معلم (Override).

## ۲. چه قابلیت‌هایی در این فاز پیاده‌سازی شدند؟

- ترکیب `image_quality` + `extraction_confidence` + `grading_confidence` با میانگین‌گیری روی منابع موجود (منابعی که `None` هستند نادیده گرفته می‌شوند)
- سه سطح توصیفی برای نمایش در پنل معلم: `auto` (>=۹۰)، `suggested` (۷۰-۸۹)، `needs_review` (<۷۰) از طریق تابع `confidence_tier()`
- قانون محافظتی: اگر یک نتیجه قبلاً توسط معلم Override شده باشد (`TEACHER_OVERRIDDEN`)، `ConfidenceEngine` هرگز آن را بازنویسی نمی‌کند
- `ReviewQueue.filter_needing_review()` برای استخراج فقط موارد `NEEDS_REVIEW` از یک لیست نتایج
- `ReviewQueue.apply_teacher_override()` برای ثبت تصمیم نهایی معلم، با اعتبارسنجی سخت‌گیرانه بازه نمره (`[0, max_score]`)

## ۳. چه فایل‌هایی ایجاد یا تغییر کردند؟

**فایل‌های جدید:**

```
confidence/confidence_engine.py
confidence/review_queue.py
tests/unit/test_confidence_engine.py
tests/unit/test_review_queue.py
.gitignore
```

**فایل‌های تغییریافته:** هیچ‌کدام از فایل‌های فازهای قبل تغییر نکردند (این فاز کاملاً افزایشی/additive بود).

## ۴. هر فایل چه مسئولیتی دارد؟

| فایل | مسئولیت |
|---|---|
| `confidence/confidence_engine.py` | ترکیب چند منبع confidence به یک نتیجه واحد + تعیین `GradingStatus` نهایی؛ همچنین `confidence_tier()` برای سطح‌بندی نمایشی سه‌گانه |
| `confidence/review_queue.py` | فیلتر کردن نتایج نیازمند بازبینی + اعمال Override دستی معلم با اعتبارسنجی |
| `.gitignore` | نادیده گرفتن `__pycache__`، دیتابیس SQLite محلی (`*.db`)، محیط مجازی، `.env`، `.pytest_cache` و غیره |

## ۵. چه تصمیم‌های معماری مهمی گرفته شد؟

1. **`app/routers/review.py` عمداً از این فاز حذف و به فاز ۵ منتقل شد.** طبق فازبندی اولیه قرار بود این فاز شامل یک Router API هم باشد، اما چون `GradeResult` هنوز هیچ‌جا در دیتابیس ذخیره نمی‌شود (این کار در فاز ۵ همراه با تصحیح دسته‌ای/تکی انجام می‌شود)، ساختن یک endpoint API که چیزی برای واکشی ندارد، کدی بدون کاربرد واقعی تولید می‌کرد. منطق `ReviewQueue` به‌صورت خالص (عملیات روی لیست در حافظه) ساخته شد تا مستقل از این‌که داده از کجا می‌آید، قابل تست و استفاده مجدد باشد؛ اتصال به دیتابیس/API فقط سیم‌کشی اضافه در فاز ۵ خواهد بود.

2. **تمایز سه‌گانه (auto/suggested/needs_review) در `status` اعمال نشد، بلکه در یک تابع جدا (`confidence_tier`) قرار گرفت.** چون `GradingStatus` (طراحی‌شده در فاز ۰) فقط دو حالت عملیاتی معنادار دارد (`GRADED` قابل استفاده / `NEEDS_REVIEW` نیازمند توقف)، افزودن یک enum سوم فقط برای یک برچسب نمایشی، منطق بقیه سیستم (مثلاً فاز ۵ که بر اساس status فیلتر می‌کند) را بی‌دلیل پیچیده می‌کرد. تصمیم گرفته شد `confidence.final_score` عدد خام را نگه دارد و لایه نمایش (API/UI) با همان دو آستانه، سه سطح را خودش بسازد.

3. **`ConfidenceEngine.evaluate()` هرگز `TEACHER_OVERRIDDEN` را بازنویسی نمی‌کند.** این یک قانون Audit Trail است: وقتی معلم دستی تصمیم گرفت، هیچ محاسبه خودکار بعدی (حتی اگر این تابع دوباره روی همان نتیجه صدا زده شود) نباید آن را لغو کند.

4. **Immutability به‌جای تغییر درجا.** هم `ConfidenceEngine.evaluate()` و هم `ReviewQueue.apply_teacher_override()` یک نسخه *جدید* از `GradeResult` برمی‌گردانند (`model_copy`) و ورودی اصلی را تغییر نمی‌دهند - سازگار با این‌که Pydantic models در این پروژه به‌عنوان داده غیرقابل‌تغییر دامنه استفاده می‌شوند.

5. **آستانه نمره معلم اعتبارسنجی سخت‌گیرانه دارد، نه فقط هشدار.** حتی معلم هم نمی‌تواند بیشتر از `max_score` سؤال، نمره override بدهد - این جلوی خطای تایپی ساده (مثلاً وارد کردن ۲۰ به‌جای ۲) را در همان لحظه می‌گیرد.

## ۶. چه وابستگی‌ها و کتابخانه‌هایی اضافه شدند؟

هیچ وابستگی جدیدی اضافه نشد - این فاز فقط از قابلیت‌های موجود Pydantic (`model_copy`) استفاده کرد.

## ۷. چه تست‌هایی انجام شدند و نتیجه آن‌ها چه بود؟

**تست‌های جدید این فاز** (۱۲ تست، همه Unit، بدون نیاز به دیتابیس یا LLM):

- `test_confidence_engine.py` (۸ تست): confidence بالا (فقط منبع Grading)، confidence متوسط (سطح suggested)، confidence پایین (NEEDS_REVIEW)، مرز دقیق ۷۰ (باید GRADED باشد)، مرز درست زیر ۷۰ (باید NEEDS_REVIEW باشد)، ترکیب سه منبع مختلف با میانگین‌گیری صحیح، عدم بازنویسی `TEACHER_OVERRIDDEN`، مرزهای `confidence_tier`
- `test_review_queue.py` (۴ تست): فیلتر صحیح فقط موارد NEEDS_REVIEW، اعمال صحیح Override (نمره/دلیل/status)، رد نمره بیش‌ازحد، رد نمره منفی

**وضعیت اجرا:** نکته: مثل فازهای قبل، در این محیط دسترسی شبکه برای نصب/اجرای واقعی `pytest` وجود نداشت - فقط `python -m py_compile` روی همه فایل‌ها (شامل ۱۲ تست جدید) بدون خطا اجرا شد. **اجرای واقعی pytest همچنان باید توسط کاربر روی سیستم محلی تأیید شود.**

## ۸. چه مواردی عمداً برای فازهای بعدی باقی مانده‌اند؟

- **اتصال واقعی `ConfidenceEngine`/`ReviewQueue` به جریان تصحیح دسته‌ای** (فراخوانی بعد از `GradingOrchestrator.grade_question()`) → Phase 5
- **`app/routers/review.py`** (endpoint های `GET /review-queue`, `POST /review-queue/{result_id}/override`) → Phase 5، بعد از این‌که `GradeResult` قابل ذخیره شد
- **`GradeResultRepository`** برای ذخیره/بازخوانی نتایج تصحیح از دیتابیس → Phase 5
- **پر کردن واقعی `image_quality`/`extraction_confidence`** → بعد از MVP، وقتی Image Quality Pipeline و OCR اضافه شوند؛ `ConfidenceEngine` از قبل برای پذیرفتن این مقادیر آماده است و نیازی به تغییر نخواهد داشت

## ۹. وضعیت فعلی پروژه برای شروع Phase 5 چگونه است؟

آماده، **مشروط به تأیید نتیجه سبز `pytest` توسط کاربر روی سیستم محلی** (طبق بند ۷).

از نظر معماری، Phase 5 (تصحیح دسته‌ای/تکی + Aggregator) اکنون می‌تواند مستقیماً از سه بلوک آماده استفاده کند:
- `GradingOrchestrator.grade_question()` از فاز ۲/۳ → تولید `GradeResult` خام
- `ConfidenceEngine.evaluate()` از فاز ۴ → تکمیل confidence و تعیین status نهایی
- `ReviewQueue` از فاز ۴ → آماده برای فیلتر/Override همین که نتایج قابل ذخیره شدند

هیچ Blocker شناخته‌شده‌ای وجود ندارد.
