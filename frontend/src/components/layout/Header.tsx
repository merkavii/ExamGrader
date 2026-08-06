// * ==============================================================================
// *                                Header
// * ==============================================================================
import { Moon, Sun } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useTheme } from "@/hooks/useTheme";

export function Header() {
  const { theme, toggleTheme } = useTheme();

  return (
    <header className="flex h-16 items-center justify-between border-b bg-card px-5">
      <div />
      <Button variant="ghost" size="icon" onClick={toggleTheme} aria-label="تغییر حالت روشن/تیره">
        {theme === "dark" ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
      </Button>
    </header>
  );
}
