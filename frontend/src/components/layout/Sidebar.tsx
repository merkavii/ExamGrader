// * ==============================================================================
// *                              Sidebar
// * ==============================================================================
// ? ساختار کلی از shadcn-admin الهام گرفته شده (Sidebar ثابت سمت راست در RTL،
// ? آیتم‌های فعال Highlight شده) اما با هویت اختصاصی: آیکون و رنگ متفاوت،
// ? بدون آیتم‌های غیرمرتبط (Mail/Chat/Calendar که در پنل‌های عمومی هست).

import { NavLink } from "react-router-dom";
import { GraduationCap, LayoutDashboard, ListChecks, School, Users } from "lucide-react";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { to: "/", label: "داشبورد", icon: LayoutDashboard, end: true },
  { to: "/classes", label: "کلاس‌ها", icon: School },
  { to: "/students", label: "دانش‌آموزان", icon: Users },
  { to: "/exams", label: "آزمون‌ها", icon: GraduationCap },
  { to: "/review-queue", label: "صف بازبینی", icon: ListChecks },
];

export function Sidebar() {
  return (
    <aside className="hidden w-64 shrink-0 border-l bg-card md:flex md:flex-col">
      <div className="flex h-16 items-center gap-2 border-b px-5">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary text-primary-foreground">
          <GraduationCap className="h-5 w-5" />
        </div>
        <div>
          <p className="text-sm font-bold leading-tight">دستیار تصحیح آزمون</p>
          <p className="text-xs text-muted-foreground">سامانه هوشمند</p>
        </div>
      </div>

      <nav className="flex-1 space-y-1 p-3">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
              )
            }
          >
            <item.icon className="h-4 w-4" />
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
