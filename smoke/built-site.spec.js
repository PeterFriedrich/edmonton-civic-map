import { expect, test } from "@playwright/test";

// Every check fails on any console error, failed request, or code/style file
// without a content hash (a stale file a browser could hold across a deploy).
function watch(page) {
  const problems = [];
  page.on("console", (m) => { if (m.type() === "error") problems.push(`console: ${m.text()}`); });
  page.on("pageerror", (e) => problems.push(`page error: ${e.message}`));
  page.on("requestfailed", (r) => {
    // MapLibre cancels tile reads it no longer needs when the camera moves.
    if (r.failure()?.errorText !== "net::ERR_ABORTED") problems.push(`failed: ${r.url()} ${r.failure()?.errorText}`);
  });
  page.on("response", (r) => { if (r.status() >= 400) problems.push(`HTTP ${r.status()}: ${r.url()}`); });
  const code = [];
  page.on("request", (r) => {
    const path = new URL(r.url()).pathname;
    if (/\.(js|mjs|css)$/.test(path)) code.push(path);
  });
  return {
    code,
    check() {
      expect(code.length, "no code was fetched").toBeGreaterThan(0);
      expect(code.filter((p) => !/-[A-Za-z0-9_-]{8}\.(js|mjs|css)$/.test(p)), "unhashed code or styles").toEqual([]);
      expect(problems).toEqual([]);
    },
  };
}

// The lookup: a typed address gives its cards before and without the map. The
// address is one of the eight split ones (docs/SPEC_data_schema.md §9.3), so
// both provincial divisions must show.
test("an address lookup shows every level, then the map draws", async ({ page }) => {
  const w = watch(page);
  await page.goto("./");
  await page.getByRole("combobox", { name: "Address" }).fill("10024 124 st");
  await page.getByRole("option", { name: "10024 124 Street NW" }).click();
  const results = page.locator("#results");
  await expect(results.getByRole("heading", { name: "10024 124 Street NW" })).toBeVisible();
  await expect(results).toContainText("more than one provincial electoral division");
  for (const role of ["Councillor", "Mayor", "Trustee", "Member of the Legislative Assembly", "Member of Parliament"]) {
    await expect(results.locator(".role", { hasText: new RegExp(`^${role}$`) }).first()).toBeVisible();
  }
  await expect(results.locator(".card")).toHaveCount(7); // 5 levels, the mayor, and the second division
  await expect(page.locator("#map-status")).toBeEmpty({ timeout: 45_000 });
  expect(w.code.some((p) => p.includes("maplibre-gl-worker")), "the map worker was not fetched").toBe(true);

  // A map click looks the point up in the browser.
  await page.locator("#map canvas").click();
  await expect(results.getByRole("heading", { name: /^Map point/ })).toBeVisible();
  w.check();
});

// The building-tiles test page, kept for phone measurements.
test("the building-tiles test page draws", async ({ page }) => {
  const w = watch(page);
  await page.goto("./buildings-test.html");
  await expect(page.locator("#loaded")).toContainText("after the page started", { timeout: 45_000 });
  await expect(page.locator("#range")).toContainText("206");
  w.check();
});
