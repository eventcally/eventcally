const { test, expect } = require("../fixtures");
const { screenshot, authorize } = require("../fixtures/helpers");

test.describe("OAuth2 token", () => {
  test("lists and revokes", async ({ page, login }) => {
    await authorize(page, login);

    await page.goto("/user/oauth2_tokens");
    await screenshot(page, "list");

    await page.locator("a[href$=revoke]").first().click();

    await screenshot(page, "revoke");
    await page.locator("#submit").click();

    await expect(page).toHaveURL(/\/user\/oauth2_tokens/);
    await expect(page.locator("a[href$=revoke]")).toHaveCount(0);
  });
});
