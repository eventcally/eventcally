const { test, expect } = require("../fixtures");
const { screenshot, typeahead } = require("../fixtures/helpers");
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
    await expect(page.locator("tbody tr")).toHaveCount(1);
    await screenshot(page, "incoming");

    await page.locator("[data-test=filters-toggle]").click();
    await page.locator("#review_status").selectOption({ label: "Abgelehnt" });
    await page.getByRole("button", { name: "Aktualisieren" }).click();
    await expect(page).toHaveURL(/review_status=3/);
    await expect(page.locator("tbody tr")).toHaveCount(0);
    await screenshot(page, "incoming-filtered");
  });

  test("reviews from the list", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    createIncomingReferenceRequest(adminUnitId);

    await page.goto(`/manage/admin_unit/${adminUnitId}/incoming_event_reference_requests`);
    await expect(page.locator("tbody tr")).toHaveCount(1);
    await page.locator("tbody .row-actions button").first().click();
    await page.getByRole("menuitem", { name: "Anfrage prüfen" }).click();
    await expect(page).toHaveURL(/incoming_event_reference_request\/\d+\/review/);
  });

  test("creates", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    createAdminUnit("test@test.de", "Other Crew");
    const eventId = createEvent(adminUnitId);

    await page.goto(
      `/manage/admin_unit/${adminUnitId}/outgoing_event_reference_request/create_for_event/${eventId}`
    );
    await typeahead(page, "admin_unit", "Oth", "Other Crew");
    await screenshot(page, "create");
    await page.locator("#submit").click();
    await expect(page).toHaveURL(
      new RegExp(`/manage/admin_unit/${adminUnitId}/outgoing_event_reference_requests`)
    );
    await screenshot(page, "outgoing");
  });
});
