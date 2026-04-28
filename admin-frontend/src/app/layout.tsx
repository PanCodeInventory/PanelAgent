import type { Metadata } from "next";
import { DM_Sans, JetBrains_Mono } from "next/font/google";
import Link from "next/link";
import { Shield, Settings, History, ClipboardCheck, LayoutDashboard } from "lucide-react";
import { LogoutButton } from "@/components/logout-button";
import { adminPath } from "@/lib/admin-path";
import "./globals.css";

const dmSans = DM_Sans({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "PanelAgent Admin",
  description: "管理后台 - PanelAgent 流式配色助手",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="zh-CN"
      className={`${dmSans.variable} ${jetbrainsMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex font-sans">
        {/* Admin Sidebar */}
        <aside className="w-64 bg-sidebar border-r border-sidebar-border flex flex-col">
          {/* Admin Banner */}
          <div className="h-16 flex items-center gap-3 px-4 border-b border-sidebar-border">
            <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
              <Shield className="w-5 h-5 text-primary-foreground" />
            </div>
            <div className="flex flex-col">
              <span className="text-sm font-semibold text-sidebar-foreground">
                PanelAgent
              </span>
              <span className="text-xs text-muted-foreground font-mono">
                ADMIN
              </span>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 p-4 space-y-1">
            <Link
              href={adminPath("/")}
              className="flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground transition-colors"
            >
              <LayoutDashboard className="w-4 h-4" />
              控制台
            </Link>
            <Link
              href={adminPath("/settings")}
              className="flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground transition-colors"
            >
              <Settings className="w-4 h-4" />
              系统设置
            </Link>
            <Link
              href={adminPath("/history")}
              className="flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground transition-colors"
            >
              <History className="w-4 h-4" />
              方案历史
            </Link>
            <Link
              href={adminPath("/quality-registry")}
              className="flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground transition-colors"
            >
              <ClipboardCheck className="w-4 h-4" />
              质量管理
            </Link>
          </nav>

          {/* Logout Button */}
          <div className="p-4 border-t border-sidebar-border">
            <LogoutButton />
          </div>
        </aside>

        {/* Main Content */}
        <div className="flex-1 flex flex-col bg-background">
          {/* Top Header */}
          <header className="h-16 border-b border-border flex items-center justify-between px-6">
            <h1 className="text-lg font-semibold text-foreground">
              管理后台
            </h1>
            <div className="flex items-center gap-4">
              <span className="text-sm text-muted-foreground">
                管理员
              </span>
              <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center">
                <span className="text-sm font-medium text-muted-foreground">
                  A
                </span>
              </div>
            </div>
          </header>

          {/* Page Content */}
          <main className="flex-1 p-6 overflow-auto">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
