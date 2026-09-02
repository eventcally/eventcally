// ported from cypress/e2e/event_place.cy.js
const { test, expect } = require("../fixtures");
const { screenshot } = require("../fixtures/helpers");
const { createAdminUnit, createEventPlace } = require("../fixtures/flask");

test.describe("Event place", () => {
  test("creates", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    await page.goto(`/manage/admin_unit/${adminUnitId}/event_place/create`);
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
    await screenshot(page, "update");
    await page.locator("#submit").click();
    await expect(page).toHaveURL(new RegExp(`/manage/admin_unit/${adminUnitId}/event_places`));
  });

  test("deletes", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    const eventPlaceId = createEventPlace(adminUnitId);
    await page.goto(`/manage/admin_unit/${adminUnitId}/event_place/${eventPlaceId}/delete`);
    await page.locator("#name").fill("Mein Platz");
    await screenshot(page, "delete");
    await page.locator("#submit").click();
    await expect(page).toHaveURL(new RegExp(`/manage/admin_unit/${adminUnitId}/event_places`));
  });
});
