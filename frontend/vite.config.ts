import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  base: process.env.BASE_PATH ?? "/",
  plugins: [react()],
  server: {
    proxy: {
      "/edinet": {
        target: "https://disclosure.edinet-fsa.go.jp",
        changeOrigin: true,
        secure: true,
        rewrite: (path) => path.replace(/^\/edinet/, ""),
      },
    },
  },
});
