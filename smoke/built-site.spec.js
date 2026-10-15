import { expect, test } from "@playwright/test";

// Loads the built page, waits for the map's first full draw, and fails on any
// console error, failed request, or code/style file without a content hash
// (a stale file a browser could hold across a deploy).
test("built page draws the map with only hashed code", async ({ page }) => {
  const problems = [];
  page.on("console", (m) => { if (m.type() === "error") problems.push(`console: ${m.text()}`); });
  page.on("pageerror", (e) => problems.push(`page error: ${e.message}`));
  page.on("requestfailed", (r) => problems.push(`failed: ${r.url()} ${r.failure()?.errorText}`));
  page.on("response", (r) => { if (r.status() >= 400) problems.push(`HTTP ${r.status()}: ${r.url()}`); });
  const code = [];
  page.on("request", (r) => {
    const path = new URL(r.url()).pathname;
    if (/\.(js|mjs|css)$/.test(path)) code.push(path);
  });

  await page.goto("./");
  await expect(page.locator("#loaded")).toContainText("after the page started", { timeout: 45_000 });
  await expect(page.locator("#range")).toContainText("206");

  expect(code.length, "no code was fetched").toBeGreaterThan(0);
  expect(code.some((p) => p.includes("maplibre-gl-worker")), "the map worker was not fetched").toBe(true);
  expect(code.filter((p) => !/-[A-Za-z0-9_-]{8}\.(js|mjs|css)$/.test(p)), "unhashed code or styles").toEqual([]);
  expect(problems).toEqual([]);
});
