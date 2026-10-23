const { test, expect } = require("../fixtures");
const { screenshot, screenshotDatepicker } = require("../fixtures/helpers");
const {
  createAdminUnit,
  createAdminUnitOrganizationInvitation,
  createAdminUnitMemberInvitation,
  createEvent,
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

    await page.goto(`/manage/admin_unit/${adminUnitId}`);
    await expect(page).toHaveURL(new RegExp(`/manage/admin_unit/${adminUnitId}/events`));
    const row = page.getByRole("cell", { name: "Name" }).first();
    await expect(row).toBeVisible();
    await screenshot(page, "events");

    await page.getByRole("button", { name: "Weitere Filter" }).click();
    await screenshot(page, "search-form");
    await page.getByRole("button", { name: "Weitere Filter" }).click();

    // The filter lives in the URL and narrows the list.
    await page.locator("#keyword").fill("Gibtesnicht");
    await page.getByRole("button", { name: "Veranstaltungen finden" }).click();
    await expect(page).toHaveURL(/keyword=Gibtesnicht/);
    await expect(page.getByText("Keine Veranstaltungen gefunden")).toBeVisible();

    await page.getByRole("button", { name: "Zurücksetzen" }).click();
    await expect(page.getByRole("cell", { name: "Name" }).first()).toBeVisible();

    // The name opens the action menu, which leads to the (Jinja) edit page.
    await page.getByRole("button", { name: "Name" }).first().click();
    await page.locator("a.dropdown-item", { hasText: "Bearbeiten" }).click();
    await expect(page).toHaveURL(/\/event\/\d+\/update/);
  });
});
