import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const localAccessToken = process.env.LOCAL_DEV_ACCESS_TOKEN;

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // All /api requests are forwarded to the FastAPI backend.
      // The frontend never calls broker or market-data APIs directly.
      "/api": {
        target: process.env.BACKEND_URL ?? "http://localhost:8000",
        changeOrigin: true,
        headers: localAccessToken ? { "X-Local-Access-Token": localAccessToken } : undefined,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
});
