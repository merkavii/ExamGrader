// * ==============================================================================
// *                    Loading / Empty / Error States
// * ==============================================================================
// ? یک نسخه یکپارچه از این سه وضعیت که در همه صفحه‌ها استفاده می‌شود - طبق
// ? قانون صریح پروژه: "Loading/Empty/Error State یکپارچه باشد".

import { AlertCircle, Inbox, Loader2 } from "lucide-react";
import type { ReactNode } from "react";
import { ApiError } from "@/api/client";
import { cn } from "@/lib/utils";

export function LoadingState({ label = "در حال بارگذاری..." }: { label?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 py-16 text-muted-foreground">
      <Loader2 className="h-6 w-6 animate-spin" />
      <p className="text-sm">{label}</p>
    </div>
  );
}

export function EmptyState({
  title,
  description,
  action,
}: {
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-lg border border-dashed py-16 text-center">
      <Inbox className="h-8 w-8 text-muted-foreground" />
      <div className="space-y-1">
        <p className="font-medium">{title}</p>
        {description && <p className="text-sm text-muted-foreground">{description}</p>}
      </div>
      {action}
    </div>
  );
}

export function ErrorState({ error, className }: { error: unknown; className?: string }) {
  // ? پیام خطای واقعی از ApiError (که خودش از پاسخ FastAPI ساخته شده) استخراج
  // ? می‌شود - نه یک پیام عمومی بی‌ربط.
  const message = error instanceof ApiError ? error.detail : "خطایی غیرمنتظره رخ داد.";
  return (
    <div className={cn("flex flex-col items-center justify-center gap-2 rounded-lg border border-destructive/30 bg-destructive/5 py-12 text-center", className)}>
      <AlertCircle className="h-6 w-6 text-destructive" />
      <p className="text-sm text-destructive">{message}</p>
    </div>
  );
}
