import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Minimal config - no basePath, no rewrites
  // External /admin prefix handled by reverse-proxy layer
};

export default nextConfig;
