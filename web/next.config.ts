import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  trailingSlash: true,
  experimental: { cpus: 2 },
  // STATIC_EXPORT=1 builds a plain static site into out/ for hosts without a Node server.
  ...(process.env.STATIC_EXPORT
    ? { output: "export" as const }
    : { cacheComponents: true, partialPrefetching: true }),
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
