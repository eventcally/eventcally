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

  test("update user roles", async ({ page, login }) => {
    createUser("admin@test.de", "password", true);
    createUser("other@test.de", "password");
    await login("admin@test.de");

    await page.goto("/admin-next/users");
    const row = page.locator("table tbody tr", { hasText: "other@test.de" });
    await row.locator("a", { hasText: /^\s*(Edit|Bearbeiten)\s*$/ }).click();

    await expect(page).toHaveURL(/\/admin-next\/users\/\d+\/update/);
    const admin = page.getByLabel(/^Administrator/);
    await expect(admin).not.toBeChecked();
    await admin.check();
    await page.locator("button[type=submit]").click();

    await expect(page.locator(".toast")).toBeVisible();
    await expect(page).toHaveURL(/\/admin-next\/users$/);

    await row.locator("a", { hasText: /^\s*(Edit|Bearbeiten)\s*$/ }).click();
    await expect(page.getByLabel(/^Administrator/)).toBeChecked();
  });

  test("delete user", async ({ page, login }) => {
    createUser("admin@test.de", "password", true);
    createUser("other@test.de", "password");
    await login("admin@test.de");

    await page.goto("/admin-next/users");
    const row = page.locator("table tbody tr", { hasText: "other@test.de" });
    await row.locator("button", { hasText: /^\s*(Delete|Löschen)\s*$/ }).click();

    const modal = page.locator(".modal.show");
    const ok = modal.locator(".btn-danger");
    await expect(ok).toBeDisabled();
    await modal.locator("input").fill("OTHER@test.de");
    await expect(ok).toBeEnabled();
    await ok.click();

    await expect(page.locator(".toast")).toBeVisible();
    await expect(row).toHaveCount(0);
  });
});
