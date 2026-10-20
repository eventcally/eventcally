const { test, expect } = require("../fixtures");
const { createUser } = require("../fixtures/flask");

test.describe("Admin (Vue 3)", () => {
  test("users", async ({ page, login }) => {
    createUser("admin@test.de", "password", true);
    await login("admin@test.de");

    await page.goto("/admin-next/users");
    await expect(page.locator("table tbody tr", { hasText: "admin@test.de" })).toBeVisible();
  });

  test("navigate from home to users without reload", async ({ page, login }) => {
    createUser("admin@test.de", "password", true);
    await login("admin@test.de");

    await page.goto("/admin-next");
    await page.evaluate(() => {
      window.__noReload = true;
    });
    await page.locator("a.list-group-item", { hasText: /^\s*(Users|Nutzer)\s*$/ }).click();

    await expect(page).toHaveURL(/\/admin-next\/users/);
    await expect(page.locator("table tbody tr", { hasText: "admin@test.de" })).toBeVisible();
    expect(await page.evaluate(() => window.__noReload)).toBe(true);
  });
});
