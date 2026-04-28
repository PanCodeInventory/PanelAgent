"use client";

import { LogOut } from "lucide-react";
import { adminPost } from "@/lib/api/admin-client";
import { adminPath } from "@/lib/admin-path";

export function LogoutButton() {
  const handleLogout = async () => {
    try {
      await adminPost("/auth/logout");
    } finally {
      window.location.href = adminPath("/login");
    }
  };

  return (
    <button
      onClick={handleLogout}
      className="w-full flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium text-sidebar-foreground hover:bg-destructive/10 hover:text-destructive transition-colors"
    >
      <LogOut className="w-4 h-4" />
      退出登录
    </button>
  );
}
