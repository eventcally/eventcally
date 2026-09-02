const { test, expect } = require("../fixtures");
const { createUser, createAdminUnit } = require("../fixtures/flask");

test.describe("Admin", () => {
  test("settings", async ({ page, login }) => {
    createUser("admin@test.de", "password", true);
    await login("admin@test.de");
    await page.goto("/admin");
    await page.goto("/admin/settings");
    await page.locator("#submit").click();
    await expect(page).toHaveURL(/\/admin/);
  });

  test("admin units", async ({ page, login }) => {
    createUser("admin@test.de", "password", true);
    await login("admin@test.de");
    await page.goto("/admin/organizations");

    const adminUnitId = createAdminUnit();
    await page.goto(`/admin/organization/${adminUnitId}/update`);
    await page.locator("#submit").click();
    await expect(page).toHaveURL(/\/admin\/organizations/);
  });

  test("users", async ({ page, login }) => {
    const userId = createUser("admin@test.de", "password", true);
    await login("admin@test.de");
    await page.goto("/admin/users");

    await page.goto(`/admin/user/${userId}/update`);
    await page.locator("#submit").click();
    await expect(page).toHaveURL(/\/admin\/users/);
  });
});
