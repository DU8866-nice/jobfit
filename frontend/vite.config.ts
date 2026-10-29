import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// In development the API runs separately on port 8000; Vite forwards /api to it.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": "http://localhost:8000",
    },
  },
});
