/// <reference types="vite/client" />

// ? تایپ متغیرهای محیطی سفارشی پروژه (VITE_API_BASE_URL) - بدون این فایل،
// ? import.meta.env در client.ts هیچ Type ای نداشت.
interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
