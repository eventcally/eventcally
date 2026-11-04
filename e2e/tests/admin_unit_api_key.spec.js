const { test, expect } = require("../fixtures");
const { screenshot } = require("../fixtures/helpers");
const { createAdminUnit } = require("../fixtures/flask");

async function createKey(page, adminUnitId, name = "Mein API Key") {
  await page.goto(`/manage/admin_unit/${adminUnitId}/api_key/create`);
  await page.locator("#name").fill(name);
  await page.locator("#submit").click();
  await expect(page).toHaveURL(/\/api_key\/\d+$/);
}

test.describe("Admin Unit API Key", () => {
  test("creates and shows the key once", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();

    await page.goto(`/manage/admin_unit/${adminUnitId}/api_key/create`);
    await screenshot(page, "create");
    await page.locator("#name").fill("Mein API Key");
    await page.locator("#submit").click();

    await expect(page).toHaveURL(/\/api_key\/\d+$/);
    await expect(page.locator("[data-test=created-key]")).toBeVisible();
    await screenshot(page, "read-after-create");

    await page.reload();
    await expect(page.locator("[data-test=created-key]")).toHaveCount(0);
    await expect(page.getByText("Mein API Key").first()).toBeVisible();
  });

  test("lists", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    await createKey(page, adminUnitId);

    await page.goto(`/manage/admin_unit/${adminUnitId}/api_keys`);
    await expect(page.locator("tbody tr")).toHaveCount(1);
    await expect(page.locator(".b-overlay")).toHaveCount(0);
    await screenshot(page, "list");
  });

  test("renames in a modal of the read page", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    await createKey(page, adminUnitId);

    await page.reload();
    await page.getByRole("button", { name: "Aktionen" }).click();
    await page.locator(".dropdown-menu.show .dropdown-item", { hasText: "Bearbeiten" }).click();
    await page.locator(".modal.show #name").fill("Neuer Name");
    await screenshot(page, "update");
    await page.locator(".modal-footer").getByRole("button", { name: "Aktualisieren" }).click();

    await expect(page.getByText("API Schlüssel erfolgreich aktualisiert")).toBeVisible();
    await expect(page.locator("dl")).toContainText("Neuer Name");
  });

  test("deletes in a modal of the list", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    await createKey(page, adminUnitId);

    await page.goto(`/manage/admin_unit/${adminUnitId}/api_keys`);
    await page.locator("tbody tr .row-actions button").first().click();
    await page.locator(".dropdown-menu.show .dropdown-item", { hasText: "Löschen" }).click();
    await page.locator(".modal input").fill("Falscher Name");
    await page.locator(".modal button[type=submit]").click();
    await expect(page.locator(".modal .invalid-feedback")).toBeVisible();
    await screenshot(page, "delete-mismatch");

    await page.locator(".modal input").fill("Mein API Key");
    await page.locator(".modal button[type=submit]").click();
    await expect(page.getByText("API Schlüssel erfolgreich gelöscht")).toBeVisible();
    await expect(page.locator("tbody tr")).toHaveCount(0);
  });

  test("deletes from the read page and returns to the list", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    await createKey(page, adminUnitId);

    await page.reload();
    await page.getByRole("button", { name: "Aktionen" }).click();
    await page.locator(".dropdown-menu.show .dropdown-item", { hasText: "Löschen" }).click();
    await page.locator(".modal input").last().fill("Mein API Key");
    await page.locator(".modal button[type=submit]").last().click();

    await expect(page).toHaveURL(new RegExp(`/manage/admin_unit/${adminUnitId}/api_keys$`));
    await expect(page.getByText("API Schlüssel erfolgreich gelöscht")).toBeVisible();
  });

  test("the removed update and delete pages are gone", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    await createKey(page, adminUnitId);
    const readUrl = page.url();

    for (const action of ["update", "delete"]) {
      const response = await page.goto(`${readUrl}/${action}`);
      expect(response.status()).toBe(404);
    }
  });
});
