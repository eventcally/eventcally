// ported from cypress/e2e/oauth2_token.cy.js
const { test, expect } = require("../fixtures");
const { screenshot, authorize } = require("../fixtures/helpers");

test.describe("OAuth2 token", () => {
  test("lists and revokes", async ({ page, login }) => {
    await authorize(page, login);

    await page.goto("/user/oauth2_tokens");
    await screenshot(page, "list");

    await page.locator(".dropdown-toggle.btn-link").click();
    await page.locator("a[href$=revoke]").click({ force: true });

    await screenshot(page, "revoke");
    await page.locator("#submit").click();

    await expect(page).toHaveURL(/\/user\/oauth2_tokens/);
  });
});
