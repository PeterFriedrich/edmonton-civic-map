import { defineConfig } from "@playwright/test";

// The browser check on the built site (docs/WEB_CACHE_BUSTING.md, "Guard it"):
// runs against `vite preview` of dist/, so it sees what Pages will serve.
export default defineConfig({
  testDir: "smoke",
  timeout: 60_000,
  reporter: "list",
  use: { baseURL: "http://127.0.0.1:4173/" },
  webServer: {
    command: "npx vite preview --host 127.0.0.1 --port 4173 --strictPort",
    url: "http://127.0.0.1:4173/",
    reuseExistingServer: false,
  },
});
