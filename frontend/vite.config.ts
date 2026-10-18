import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// `npm run build:pages` builds the static GitHub Pages demo (mode "pages") into ../docs.
export default defineConfig(({ mode }) => ({
  base: mode === "pages" ? "/Bill-Sight/" : "/",
  plugins: [react()],
  server: { proxy: { "/api": "http://127.0.0.1:8000" } },
}));
