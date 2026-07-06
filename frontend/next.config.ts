import path from "node:path";
import type { NextConfig } from "next";

const allowedDevOrigins = Array.from(
  new Set(
    [
      "localhost",
      "127.0.0.1",
      "192.168.1.100",
      "192.168.1.105",
      ...(process.env.ALLOWED_DEV_ORIGINS?.split(",").map((origin) => origin.trim()).filter(Boolean) ?? []),
    ],
  ),
);

// Static export is only enabled when PANELAGENT_STATIC_EXPORT=1 (set by the
// single-exe CI build). The default (Linux dev / docker server) keeps the
// standard Next.js server runtime, route handlers and SSR.
const staticExport = process.env.PANELAGENT_STATIC_EXPORT === "1";

const nextConfig: NextConfig = {
  allowedDevOrigins,
  turbopack: {
    root: path.join(__dirname),
  },
  ...(staticExport
    ? {
        output: "export" as const,
        images: { unoptimized: true },
      }
    : {}),
};

export default nextConfig;
