const { test, expect } = require("../fixtures");
const { screenshot } = require("../fixtures/helpers");
const { createAdminUnit, createIncomingReference, createEvent } = require("../fixtures/flask");

test.describe("Reference", () => {
  test("reads and outgoing", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    createIncomingReference(adminUnitId);
    await page.goto(`/manage/admin_unit/${adminUnitId}/outgoing_event_references`);
    await screenshot(page, "outgoing");
  });

  test("creates", async ({ page, login }) => {
    await login();
    createAdminUnit();
    const otherAdminUnitId = createAdminUnit("test@test.de", "Other Crew");
    const eventId = createEvent(otherAdminUnitId);

    await page.goto(`/event/${eventId}/reference`);
    await screenshot(page, "create");
    await page.locator("#submit").click();
    await expect(page).not.toHaveURL(/\/reference/);
  });

  test("updates", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    const referenceId = createIncomingReference(adminUnitId);

    await page.goto(
      `/manage/admin_unit/${adminUnitId}/incoming_event_reference/${referenceId}/update`
    );
    await screenshot(page, "update");
    await page.locator("#submit").click();
    await expect(page).toHaveURL(
      new RegExp(`/manage/admin_unit/${adminUnitId}/incoming_event_reference/${referenceId}`)
    );
    await screenshot(page, "incoming");
  });

  test("deletes", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    const referenceId = createIncomingReference(adminUnitId);

    await page.goto(
      `/manage/admin_unit/${adminUnitId}/incoming_event_reference/${referenceId}/delete`
    );
    await screenshot(page, "delete");
    await page.locator("#submit").click();
    await expect(page).toHaveURL(
      new RegExp(`/manage/admin_unit/${adminUnitId}/incoming_event_references`)
    );
  });
});
