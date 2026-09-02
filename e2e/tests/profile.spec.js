const { test, expect } = require("../fixtures");

test.describe("Profile", () => {
  test("profile", async ({ page, login }) => {
    await login();
    await page.goto("/profile");
    await expect(page.locator("h1")).toContainText("test@test.de");
  });
});
