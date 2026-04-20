import type { Metadata } from "next";
import { DM_Sans, JetBrains_Mono } from "next/font/google";
import Link from "next/link";
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
  title: "PanelAgent 流式配色助手",
  description: "结合确定性算法与AI评估，基于实验室真实库存生成有效的配色方案",
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
      <body className="min-h-full flex flex-col font-sans">
        <header className="sticky top-0 z-50 bg-background border-b border-border">
          <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
            <div className="flex items-center gap-3">
              <Link href="/" className="flex items-center gap-2 group">
                <span className="text-xl font-semibold tracking-tight text-primary transition-colors">
                  PanelAgent
                </span>
                <span className="text-xl font-light tracking-tight text-muted-foreground">
                  流式配色助手
                </span>
              </Link>
            </div>
            <nav className="flex items-center gap-1">
              <Link
                href="/"
                className="relative px-4 py-2 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
              >
                <span className="relative">
                  首页
                  <span className="absolute inset-x-0 -bottom-1 h-px bg-primary opacity-0 transition-opacity group-hover:opacity-100" />
                </span>
              </Link>
              <Link
                href="/exp-design"
                className="relative px-4 py-2 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
              >
                <span className="relative">
                  实验设计
                  <span className="absolute inset-x-0 -bottom-1 h-px bg-primary opacity-0 transition-opacity hover:opacity-100" />
                </span>
              </Link>
              <Link
                href="/panel-design"
                className="relative px-4 py-2 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
              >
                <span className="relative">
                  配色方案
                  <span className="absolute inset-x-0 -bottom-1 h-px bg-primary opacity-0 transition-opacity hover:opacity-100" />
                </span>
              </Link>
              <Link
                href="/quality-registry"
                className="relative px-4 py-2 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
              >
                <span className="relative">
                  质量登记
                  <span className="absolute inset-x-0 -bottom-1 h-px bg-primary opacity-0 transition-opacity hover:opacity-100" />
                </span>
              </Link>
            </nav>
          </div>
        </header>
        <main className="flex-1">{children}</main>
        <footer className="border-t border-border bg-background">
          <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4 text-xs text-muted-foreground sm:px-6 lg:px-8">
            <span>PanelAgent 流式配色助手</span>
            <span className="font-mono">由回溯搜索 + LLM 驱动</span>
          </div>
        </footer>
      </body>
    </html>
  );
}
