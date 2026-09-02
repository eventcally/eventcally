// ported from cypress/e2e/root.cy.js
const { test } = require("../fixtures");
const { screenshot } = require("../fixtures/helpers");
const { createAdminUnit, createEvent } = require("../fixtures/flask");

test.describe("Root", () => {
  test("simple", async ({ page }) => {
    await page.goto("/");
    await screenshot(page, "home");

    // Cypress needed `{failOnStatusCode: false}` here; Playwright does not fail
    // on a 4xx response, so a plain goto is the faithful translation.
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
