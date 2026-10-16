import { defineConfig } from "vite";

// Pages serves the site under /edmonton-civic-map/, so every URL is relative.
// site/public/ (published data, and the libraries' licences, which the minifier
// strips from the bundle) is copied as-is; everything else is bundled with
// content-hashed file names, which is the cache busting.
export default defineConfig({
  root: "site",
  base: "./",
  // MapLibre alone is about 1 MB minified; one bundle is expected for now.
  build: {
    outDir: "../dist",
    emptyOutDir: true,
    chunkSizeWarningLimit: 1200,
    // The lookup page, the about page, and the building-tiles test page kept for phone measurements.
    rolldownOptions: { input: { main: "site/index.html", about: "site/about.html", buildings: "site/buildings-test.html" } },
  },
});
