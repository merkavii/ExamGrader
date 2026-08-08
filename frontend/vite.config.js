import path from "node:path";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";
// * تنظیمات Vite: افزونه React + alias برای import های تمیز (@/components/...)
export default defineConfig({
    plugins: [react()],
    resolve: {
        alias: {
            "@": path.resolve(__dirname, "./src"),
        },
    },
    server: {
        port: 5173,
    },
});
