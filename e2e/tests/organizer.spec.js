const { test, expect } = require("../fixtures");
const { screenshot } = require("../fixtures/helpers");
const { createAdminUnit, createEventOrganizer } = require("../fixtures/flask");

test.describe("Event organizer", () => {
  test("creates", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    await page.goto(`/manage/admin_unit/${adminUnitId}/event_organizer/create`);
    await page.locator("#name").fill("Mein Veranstalter");
    await screenshot(page, "create");
    await page.locator("#submit").click();
    await expect(page).toHaveURL(
      new RegExp(`/manage/admin_unit/${adminUnitId}/event_organizers`)
    );
    await screenshot(page, "list");
  });

  test("updates", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    const eventOrganizerId = createEventOrganizer(adminUnitId);
    await page.goto(
      `/manage/admin_unit/${adminUnitId}/event_organizer/${eventOrganizerId}/update`
    );
    await screenshot(page, "update");
    await page.locator("#submit").click();
    await expect(page).toHaveURL(
      new RegExp(`/manage/admin_unit/${adminUnitId}/event_organizers`)
    );
  });

  test("deletes", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    const eventOrganizerId = createEventOrganizer(adminUnitId);
    await page.goto(
      `/manage/admin_unit/${adminUnitId}/event_organizer/${eventOrganizerId}/delete`
    );
    await page.locator("#name").fill("Mein Veranstalter");
    await screenshot(page, "delete");
    await page.locator("#submit").click();
    await expect(page).toHaveURL(
      new RegExp(`/manage/admin_unit/${adminUnitId}/event_organizers`)
    );
  });
});
