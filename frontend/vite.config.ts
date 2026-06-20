import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  // Load .env files (e.g. a gitignored frontend/.env.local) with an empty prefix
  // so the dev server can read non-VITE_ vars. process.env still takes precedence,
  // so the Docker frontend (which injects these via its service env) is unaffected.
  // These values are used ONLY by the dev proxy below — they are never bundled into
  // the client (Vite only exposes VITE_-prefixed vars to browser code).
  const fileEnv = loadEnv(mode, process.cwd(), "");
  const localAccessToken = process.env.LOCAL_DEV_ACCESS_TOKEN ?? fileEnv.LOCAL_DEV_ACCESS_TOKEN;
  const skyframeFixtureHeader = process.env.SKYFRAME_FIXTURE_HEADER ?? fileEnv.SKYFRAME_FIXTURE_HEADER;
  const skyframeDashboardState = process.env.SKYFRAME_DASHBOARD_STATE ?? fileEnv.SKYFRAME_DASHBOARD_STATE;
  const backendUrl = process.env.BACKEND_URL ?? fileEnv.BACKEND_URL ?? "http://localhost:8000";
  const proxyHeaders = {
    ...(localAccessToken ? { "X-Local-Access-Token": localAccessToken } : {}),
    ...(skyframeFixtureHeader ? { "X-Skyframe-Fixture": skyframeFixtureHeader } : {}),
    ...(skyframeDashboardState ? { "X-Skyframe-Dashboard-State": skyframeDashboardState } : {}),
  };

  return {
    plugins: [react()],
    server: {
      port: 5173,
      proxy: {
        // All /api requests are forwarded to the FastAPI backend.
        // The frontend never calls broker or market-data APIs directly.
        "/api": {
          target: backendUrl,
          changeOrigin: true,
          headers: Object.keys(proxyHeaders).length > 0 ? proxyHeaders : undefined,
          rewrite: (path) => path.replace(/^\/api/, ""),
        },
      },
    },
  };
});
