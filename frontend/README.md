# Frontend - سامانه هوشمند کمک به تصحیح آزمون

Frontend این پروژه با React + TypeScript + Vite + Tailwind CSS + shadcn/ui
(کامپوننت‌های دست‌نویس، نه CLI) ساخته شده و به Backend واقعی FastAPI متصل می‌شود.

## نصب

```bash
cd frontend
npm install
cp .env.example .env
# در صورت نیاز آدرس Backend را در .env تغییر بده (پیش‌فرض http://localhost:8000)
```

## اجرا (توسعه)

```bash
npm run dev
```

سپس روی `http://localhost:5173` باز می‌شود. Backend باید جداگانه و از قبل با
`uvicorn app.main:app --reload` روی پورت ۸۰۰۰ در حال اجرا باشد (طبق CORS
تنظیم‌شده در `app/main.py`).

## Build نسخه نهایی

```bash
npm run build
npm run preview   # برای پیش‌نمایش نسخه build شده
```

## ساختار

```
src/
├── api/          لایه مرکزی ارتباط با Backend - یک فایل به‌ازای هر روتر واقعی
├── hooks/        Hook های TanStack Query (کش/Loading/Error) روی api/
├── types/        Type های TypeScript - آینه دقیق مدل‌های Pydantic
├── components/
│   ├── ui/       کامپوننت‌های پایه (شبیه shadcn/ui)
│   ├── layout/   Sidebar, Header, AppLayout
│   └── common/   StateViews (Loading/Empty/Error)، Badge های وضعیت، PageHeader
├── pages/        صفحه‌ها - هرکدام به Route مشخص وصل است (نگاه کن به App.tsx)
└── lib/          توابع کمکی خالص (cn, formatAnswerContent)
```
