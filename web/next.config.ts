import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Allow dev-server resources (HMR, chunks) when the app is opened via
  // 127.0.0.1 rather than localhost. Next 16 blocks cross-origin dev
  // resources by default, which otherwise leaves the page blank on 127.0.0.1.
  allowedDevOrigins: ["127.0.0.1"],
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
        ],
      },
    ];
  },
};

export default nextConfig;
