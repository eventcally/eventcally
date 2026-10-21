import vue from "@vitejs/plugin-vue";
import { fileURLToPath, URL } from "node:url";
import { defineConfig } from "vitest/config";

const src = fileURLToPath(new URL("./src", import.meta.url));

export default defineConfig({
  plugins: [vue()],
  base: "/static/dist/",
  resolve: { alias: { "@": src } },
  build: {
    outDir: "../project/presentation/web/static/dist",
    emptyOutDir: true,
    manifest: true,
    rollupOptions: {
      input: { admin: "src/apps/admin/main.ts", public: "src/apps/public/main.ts" },
    },
  },
  server: { origin: "http://localhost:5173" },
  test: { environment: "jsdom", include: ["src/**/*.spec.ts", "scripts/**/*.spec.ts"] },
});
