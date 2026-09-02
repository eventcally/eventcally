const { test } = require("../fixtures");
const { screenshot } = require("../fixtures/helpers");
const { createAdminUnit, createEvent } = require("../fixtures/flask");

test.describe("Root", () => {
  test("simple", async ({ page }) => {
    await page.goto("/");
    await screenshot(page, "home");

    // /tos legitimately 404s. Playwright does not fail on a 4xx response, and
    // the console guard allows Chromium's "Failed to load resource" line.
    await page.goto("/tos");
    await screenshot(page, "tos");

    await page.goto("/legal_notice");
    await screenshot(page, "legal_notice");

    await page.goto("/contact");
    await screenshot(page, "contact");

    await page.goto("/privacy");
    await screenshot(page, "privacy");

    await page.goto("/developer");
    await screenshot(page, "developer");
  });

  test("example", async ({ page }) => {
    const adminUnitId = createAdminUnit("test@test.de", "Goslar");
    createEvent(adminUnitId);
    await page.goto("/organizations");
    await screenshot(page, "organizations");
  });
});
