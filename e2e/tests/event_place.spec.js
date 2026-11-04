const { test, expect } = require("../fixtures");
const { screenshot } = require("../fixtures/helpers");
const { createAdminUnit, createEventPlace } = require("../fixtures/flask");

test.describe("Event place", () => {
  test("creates", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    await page.goto(`/manage/admin_unit/${adminUnitId}/event_place/create`);
    await expect(page.locator("#name")).toBeVisible();
    await page.locator("#name").fill("Mein Platz");
    await screenshot(page, "create");
    await page.locator("#submit").click();
    await expect(page).toHaveURL(new RegExp(`/manage/admin_unit/${adminUnitId}/event_places`));
    await screenshot(page, "list");
  });

  test("updates", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    const eventPlaceId = createEventPlace(adminUnitId);
    await page.goto(`/manage/admin_unit/${adminUnitId}/event_place/${eventPlaceId}/update`);
    await expect(page.locator("#name")).not.toHaveValue("");
    await screenshot(page, "update");
    await page.locator("#submit").click();
    await expect(page).toHaveURL(new RegExp(`/manage/admin_unit/${adminUnitId}/event_places`));
  });

  test("deletes in a modal of the list", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    createEventPlace(adminUnitId);
    await page.goto(`/manage/admin_unit/${adminUnitId}/event_places`);
    await expect(page.getByRole("button", { name: "Mein Platz" })).toBeVisible();
    await expect(page.locator(".b-overlay")).toHaveCount(0);
    await screenshot(page, "list");

    await page.getByRole("button", { name: "Mein Platz" }).click();
    await page.locator(".dropdown-menu.show button.dropdown-item", { hasText: "Löschen" }).click();
    await page.locator("#name").fill("Falscher Name");
    await page.locator("#submit").click();
    await expect(page.locator(".modal [data-test=field-error]")).toBeVisible();

    await page.locator("#name").fill("Mein Platz");
    await screenshot(page, "delete");
    await page.locator("#submit").click();
    await expect(page.getByText("Ort erfolgreich gelöscht")).toBeVisible();
    await expect(page.getByRole("button", { name: "Mein Platz" })).toHaveCount(0);
  });
});
