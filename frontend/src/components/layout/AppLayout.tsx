// * ==============================================================================
// *                              AppLayout
// * ==============================================================================
// ? قالب اصلی همه صفحه‌ها: Sidebar ثابت + Header بالا + محتوای صفحه فعلی
// ? (از طریق <Outlet /> مسیرهای React Router). فقط اینجا Layout تعریف شده -
// ? هیچ صفحه‌ای دوباره Sidebar/Header نمی‌سازد.

import { Outlet } from "react-router-dom";
import { Header } from "./Header";
import { Sidebar } from "./Sidebar";

export function AppLayout() {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <Header />
        <main className="container flex-1 py-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
