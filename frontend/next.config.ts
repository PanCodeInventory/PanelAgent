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

const nextConfig: NextConfig = {
  // Static HTML export: produces a fully static site under ./out that can be
  // served by any static file server (including the bundled FastAPI backend
  // in the single-exe build). Disables the Next.js server runtime, route
  // handlers, SSR and image optimization.
  output: "export",
  images: {
    unoptimized: true,
  },
  allowedDevOrigins,
  turbopack: {
    root: path.join(__dirname),
  },
};

export default nextConfig;
