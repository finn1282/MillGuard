import { defineConfig, loadEnv, type Plugin } from "vite";
import react from "@vitejs/plugin-react";
import fs from "node:fs";
import path from "node:path";

// GitHub Pages has no server-side routing: serve the app for unknown paths so deep links and refreshes work.
const spaFallback = (): Plugin => ({
  name: "spa-404",
  apply: "build",
  closeBundle() {
    const out = path.resolve(__dirname, "dist");
    fs.copyFileSync(path.join(out, "index.html"), path.join(out, "404.html"));
  },
});

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "VITE_");
  const base = env.VITE_BASE || "/";
  return {
    base: base.endsWith("/") ? base : `${base}/`,
    plugins: [react(), spaFallback()],
    resolve: { alias: { "@contracts": path.resolve(__dirname, "../contracts") } },
    server: { host: true, port: 5173, fs: { allow: [".."] } },
  };
});
