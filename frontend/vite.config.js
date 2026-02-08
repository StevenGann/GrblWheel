/** Vite config: Vue 3, dev server proxies /api and /assets to backend (default 8765). */
import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  plugins: [vue()],
  base: "/",
  server: {
    port: 5173,
    proxy: {
      "/api": { target: "http://localhost:8765", changeOrigin: true },
      "/assets": { target: "http://localhost:8765", changeOrigin: true },
    },
  },
});
