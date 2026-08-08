# Answer Sheet Image Extraction - Completion Report (Post-MVP)

**پروژه:** دستیار هوشمند تصحیح آزمون (Exam Grader)
**تاریخ آخرین به‌روزرسانی:** بعد از تکمیل اولین فاز بعد از MVP (ورود پاسخ از عکس)

---

## ۱. هدف این فاز چه بود؟

اولین قابلیت بعد از MVP: امکان این‌که معلم به‌جای ورود دستی پاسخ دانش‌آموز، یک
عکس از برگه پاسخ آپلود کند و سیستم پاسخ‌های پیشنهادی را استخراج کند - با
حفظ اصل همیشگی پروژه: "معلم باید بتواند اطلاعات استخراج‌شده را قبل از ذخیره
بررسی و ویرایش کند."

## ۲. چه قابلیت‌هایی پیاده‌سازی شدند؟

- `ImageQualityChecker`: تشخیص تاری (واریانس Laplacian) و نور نامناسب قبل از OCR
- `ImagePreprocessor`: اصلاح Perspective (تشخیص لبه برگه با کانتور + warp)، Deskew،
  کاهش نویز، بهبود کنتراست (CLAHE) - همه با OpenCV، بدون هیچ تولید محتوای مصنوعی
- `OCRClient`/`TesseractOCRClient`: انتزاع مستقل از Tesseract (دقیقاً الگوی
  `LLMClient`/`OllamaProvider`) با Confidence واقعی per-line (نه یک عدد ثابت)
- `AnswerSheetExtractor`: نگاشت ترتیبی خط OCR -> سؤال، تفسیر متن بر اساس نوع
  سؤال (با استفاده از `normalize_text`/`parse_number` موجود - نه بازنویسی)،
  محاسبه Confidence ترکیبی (کیفیت تصویر + OCR + موفقیت تفسیر)
- Endpoint جدید: `POST /exams/{id}/students/{id}/answers/extract-from-image` -
  فقط پیشنهاد برمی‌گرداند، هیچ‌چیز ذخیره نمی‌کند

## ۳. فایل‌های جدید

```
ocr/ocr_client.py
ocr/tesseract_ocr_client.py
extraction/image_quality/quality_checker.py
extraction/image_quality/preprocessing_pipeline.py
extraction/answer_sheet_extractor.py
tests/unit/test_image_quality_checker.py
tests/unit/test_answer_sheet_extractor.py
tests/integration/test_answer_sheet_extraction_real_ocr.py
tests/integration/test_answer_sheet_extraction_api.py
```

## ۴. فایل‌های تغییریافته

```
config/settings.py       (+ ocr_language)
app/dependencies.py      (+ get_ocr_client, get_answer_sheet_extractor)
app/routers/sheets.py    (+ POST .../extract-from-image)
pyproject.toml           (+ opencv-python-headless, pytesseract, pillow, numpy, python-multipart)
tests/unit/fakes.py      (+ FakeOCRClient)
.gitignore               (به‌روزرسانی یادداشت - تصاویر اصلاً ذخیره نمی‌شوند)
```

## ۵. تصمیم‌های معماری مهم

1. **نگاشت خط->سؤال فقط بر اساس ترتیب است، نه تحلیل چیدمان واقعی صفحه.** این
   یک ساده‌سازی عمدی و مستند‌شده است (نه محدودیت پنهان) - تحلیل چیدمان واقعی
   یک مسئله جداگانه و پیچیده‌تر است.

2. **Confidence هر پاسخ، ترکیبی از سه عامل است**: کیفیت تصویر + اطمینان OCR
   همان خط + موفقیت تفسیر متن برای نوع سؤال. اگر تفسیر شکست بخورد (مثلاً عدد
   نامعتبر یا گزینه‌ای که با هیچ option ای نمی‌خواند)، سقف اطمینان به ۳۰
   محدود می‌شود - حتی اگر خود OCR به متنش مطمئن بود؛ چون متن واضحِ نامربوط
   بهتر از نداشتن متن نیست.

3. **هیچ تصویری ذخیره نمی‌شود.** پردازش کاملاً in-memory است.

4. **endpoint استخراج، مستقل از endpoint ثبت نهایی است.** `POST .../extract-from-image`
   فقط پیشنهاد می‌دهد؛ ثبت نهایی همچنان همان `POST .../answers` قبلی است (با
   `source="image"`) - بدون هیچ تغییری در آن endpoint.

5. **محدودیت محیط توسعه (نه کد):** بسته زبان فارسی Tesseract
   (`tesseract-ocr-fas`) در این محیط sandbox قابل نصب نبود (۴۰۳ از مخزن
   Ubuntu). Pipeline با متن انگلیسی واقعاً تست و تأیید شد (پایین‌تر). دقت
   OCR فارسی باید بعد از نصب `tesseract-ocr-fas` روی سیستم واقعی جداگانه
   بررسی شود.

## ۶. وابستگی‌های جدید

`opencv-python-headless` (پردازش تصویر)، `pytesseract` (رابط Python به
Tesseract)، `pillow` (بارگذاری/تبدیل تصویر)، `numpy` (وابستگی OpenCV)،
`python-multipart` (لازم برای `UploadFile` در FastAPI).

## ۷. تست‌ها و نتیجه واقعی اجرا (نه فقط py_compile)

برخلاف کل پروژه تا این لحظه، این‌بار بخشی از کد **واقعاً در همین محیط اجرا و
تأیید شد** - چون OpenCV/Pillow/pytesseract (برخلاف pydantic/FastAPI) از قبل
نصب بودند:

- `ImagePreprocessor` روی یک تصویر واقعی (متن چرخانده‌شده) اجرا شد - Deskew
  با موفقیت زاویه را اصلاح کرد.
- `TesseractOCRClient` (منطق گروه‌بندی خطوط) روی همان تصویر پردازش‌شده واقعاً
  OCR انگلیسی انجام داد و **۳ خط را درست تفکیک کرد** با Confidence متفاوت
  برای هرکدام (۶۶٫۰ برای خط با خطای OCR در برخورد به "Q1"، ۸۹٫۵ و ۹۲٫۵ برای دو
  خط دیگر) - این دقیقاً رفتاری است که برای تصمیم‌گیری Review Queue لازم است.
- `ImageQualityChecker` با یک باگ واقعی در تصویر تستِ اولیه (نه در خود منطق)
  پیدا و اصلاح شد - نسخه نهایی هم دستی هم به‌صورت تست واحد تأیید شد.

**تست‌های جدید نوشته‌شده (۲۲ تست):**
- `test_image_quality_checker.py` (۵ تست)
- `test_answer_sheet_extractor.py` (۱۰ تست، با `FakeOCRClient`)
- `test_answer_sheet_extraction_real_ocr.py` (۲ تست، با Tesseract واقعی/انگلیسی)
- `test_answer_sheet_extraction_api.py` (۴ تست، سطح HTTP کامل)

**آنچه هنوز تأیید نشده:** اجرای کامل `pytest` (چون `pydantic`/`fastapi` در
این محیط قابل نصب نبودند - همان محدودیت همیشگی). لطفاً محلی اجرا کن:

```bash
pip install -e ".[dev]"
apt-get install tesseract-ocr-fas   # برای OCR فارسی واقعی
pytest tests/ -v
```

## ۸. چه چیزی هنوز خارج از محدوده است

PDF به‌عنوان منبع ورودی (طبق تصمیم صریح - این فاز فقط عکس بود)، تحلیل چیدمان
واقعی صفحه (به‌جای نگاشت ترتیبی)، تشخیص دست‌خط پیشرفته (Tesseract برای
دست‌خط ضعیف عمل می‌کند - این یک محدودیت شناخته‌شده Tesseract است، نه چیزی که
این فاز حل کند)، ذخیره تصویر اصلی برای Audit، Matching/تشریحی بلند در OCR.

## ۹. Frontend

فعلاً **بدون تغییر**. برای استفاده کامل از این قابلیت، Frontend نیاز به یک
مرحله «آپلود عکس» قبل از فرم پاسخ موجود (`AnswerEntryPage`) دارد که پاسخ‌های
پیشنهادی را از `POST .../extract-from-image` بگیرد و همان فرم را از قبل پر
کند. این یک افزودن کوچک است (نه بازنویسی) چون فرم و endpoint ثبت نهایی از
قبل آماده‌اند.
