import type { HTMLAttributes } from "react";
import { cn } from "@/lib/utils";

// ? برای Loading State یکپارچه در جدول‌ها/کارت‌ها - طبق قانون بخش ششم پروژه
function Skeleton({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("animate-pulse rounded-md bg-muted", className)} {...props} />;
}

export { Skeleton };
