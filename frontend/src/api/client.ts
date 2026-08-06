// * ==============================================================================
// *                              API Client
// * ==============================================================================
// ? تنها نقطه‌ای که در کل Frontend مستقیماً fetch می‌زند و آدرس Backend را
// ? می‌داند. همه فایل‌های api/*.ts دیگر فقط از request() اینجا استفاده می‌کنند.
//
// ! هیچ کامپوننتی نباید مستقیماً fetch بزند یا آدرس API را Hardcode کند - این
// ! دقیقاً همان قانونی است که در بخش ششم خواسته شده بود.

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    public status: number,
    public detail: string
  ) {
    super(detail);
    this.name = "ApiError";
  }
}

interface RequestOptions {
  method?: "GET" | "POST" | "PUT" | "DELETE";
  body?: unknown;
  params?: Record<string, string | undefined>;
}

export async function apiRequest<TResponse>(
  path: string,
  options: RequestOptions = {}
): Promise<TResponse> {
  const url = new URL(API_BASE_URL + path);
  if (options.params) {
    for (const [key, value] of Object.entries(options.params)) {
      if (value !== undefined) url.searchParams.set(key, value);
    }
  }

  const response = await fetch(url.toString(), {
    method: options.method ?? "GET",
    headers: options.body ? { "Content-Type": "application/json" } : undefined,
    body: options.body ? JSON.stringify(options.body) : undefined,
  });

  if (!response.ok) {
    // ? FastAPI خطاهای HTTPException را به شکل {"detail": "..."} برمی‌گرداند
    // ? و خطاهای Validation را به شکل {"detail": [...]}. هر دو حالت را می‌گیریم.
    let detail = `خطای ${response.status}`;
    try {
      const errorBody = await response.json();
      if (typeof errorBody.detail === "string") {
        detail = errorBody.detail;
      } else if (Array.isArray(errorBody.detail)) {
        detail = errorBody.detail.map((e: { msg?: string }) => e.msg).join("، ");
      }
    } catch {
      // ! بدنه پاسخ JSON نبود - همان پیام پیش‌فرض بالا استفاده می‌شود
    }
    throw new ApiError(response.status, detail);
  }

  // ? برخی endpoint ها (مثلاً در آینده) ممکن است بدنه خالی برگردانند
  if (response.status === 204) return undefined as TResponse;
  return response.json() as Promise<TResponse>;
}
