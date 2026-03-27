import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "FlowCyt Panel Assistant",
  description: "Hybrid AI tool for multi-color flow cytometry panel design",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        <header className="border-b bg-background">
          <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
            <div className="flex items-center gap-2">
              <Link href="/" className="text-xl font-bold tracking-tight">
                FlowCyt Panel Assistant
              </Link>
            </div>
            <nav className="flex items-center gap-6">
              <Link
                href="/"
                className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
              >
                Home
              </Link>
              <Link
                href="/exp-design"
                className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
              >
                Experimental Design
              </Link>
              <Link
                href="/panel-design"
                className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
              >
                Panel Generation
              </Link>
            </nav>
          </div>
        </header>
        <main className="flex-1">{children}</main>
        <footer className="border-t bg-background py-6">
          <div className="mx-auto max-w-7xl px-4 text-center text-sm text-muted-foreground sm:px-6 lg:px-8">
            FlowCyt Panel Assistant — Hybrid AI for flow cytometry panel design
          </div>
        </footer>
      </body>
    </html>
  );
}
