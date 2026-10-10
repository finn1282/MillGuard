import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";

export default defineConfig({
  plugins: [react()],
  resolve: { alias: { "@contracts": path.resolve(__dirname, "../contracts") } },
  server: { host: true, port: 5173, fs: { allow: [".."] } },
});
