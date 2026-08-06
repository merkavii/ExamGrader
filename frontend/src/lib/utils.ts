import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

// ? ادغام امن کلاس‌های Tailwind (شرطی + بدون تداخل) - استاندارد shadcn/ui
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
