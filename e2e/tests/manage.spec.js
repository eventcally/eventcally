const { test, expect } = require("../fixtures");
const { screenshot, screenshotDatepicker } = require("../fixtures/helpers");
const {
  createAdminUnit,
  createAdminUnitOrganizationInvitation,
  createAdminUnitMemberInvitation,
  createEvent,
  createEventList,
} = require("../fixtures/flask");

test.describe("Manage", () => {
  test("Organizations", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    createAdminUnitOrganizationInvitation(adminUnitId, "test@test.de");
    createAdminUnitMemberInvitation(adminUnitId, "test@test.de");

    await page.goto("/manage/admin_units");
    // "Einladungen" is also a substring of "Organisationseinladungen", so this
    // matches two headings; .first() keeps it out of strict-mode trouble.
    await expect(page.locator("h1", { hasText: "Einladungen" }).first()).toBeAttached();
    await expect(
      page.locator("h1", { hasText: "Organisationseinladungen" }).first()
    ).toBeAttached();
    await expect(page.locator("h1", { hasText: "Organisationen" }).first()).toBeAttached();
    await screenshot(page, "organizations");
  });

  test("Events", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    createEvent(adminUnitId);
    createEventList(adminUnitId);

    await page.goto(`/manage/admin_unit/${adminUnitId}`);
    await expect(page).toHaveURL(new RegExp(`/manage/admin_unit/${adminUnitId}/events`));
    await screenshot(page, "events");

    await page.locator("[data-target='#search_form_container']").click();
    await screenshot(page, "search-form");
    await screenshotDatepicker(page, "#date_from-user");
    await page.locator("[data-target='#search_form_container']").click();
  });
});
