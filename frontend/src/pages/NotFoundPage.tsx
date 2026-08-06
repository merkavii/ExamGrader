import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";

export function NotFoundPage() {
  return (
    <div className="flex flex-col items-center justify-center gap-4 py-24 text-center">
      <p className="text-6xl font-bold text-muted-foreground">۴۰۴</p>
      <p className="text-lg font-medium">صفحه موردنظر پیدا نشد</p>
      <Button asChild>
        <Link to="/">بازگشت به داشبورد</Link>
      </Button>
    </div>
  );
}
