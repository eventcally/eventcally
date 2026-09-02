// ported from cypress/e2e/reference_request.cy.js
const { test, expect } = require("../fixtures");
const { screenshot, select2 } = require("../fixtures/helpers");
const {
  createAdminUnit,
  createIncomingReferenceRequest,
  createEvent,
} = require("../fixtures/flask");

test.describe("Reference request", () => {
  test("lists", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    createIncomingReferenceRequest(adminUnitId);

    await page.goto(`/manage/admin_unit/${adminUnitId}/incoming_event_reference_requests`);
    await screenshot(page, "incoming");
  });

  test("creates", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    createAdminUnit("test@test.de", "Other Crew");
    const eventId = createEvent(adminUnitId);

    await page.goto(
      `/manage/admin_unit/${adminUnitId}/outgoing_event_reference_request/create_for_event/${eventId}`
    );
    await select2(page, "admin_unit", "Oth", "Other Crew");
    await screenshot(page, "create");
    await page.locator("#submit").click();
    await expect(page).toHaveURL(
      new RegExp(`/manage/admin_unit/${adminUnitId}/outgoing_event_reference_requests`)
    );
    await screenshot(page, "outgoing");
  });
});
