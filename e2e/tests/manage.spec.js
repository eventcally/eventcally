const { test, expect } = require("../fixtures");
const { screenshot } = require("../fixtures/helpers");
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
    await expect(page.getByRole("button", { name: "Organisation erstellen" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Organisation einladen" })).toBeVisible();
    await expect(page.locator("[data-test=organizations] a", { hasText: "Meine Crew" })).toBeVisible();
    await screenshot(page, "organizations");

    // The organization link is the server side redirect to the events.
    await page.locator("[data-test=organizations] a", { hasText: "Meine Crew" }).click();
    await expect(page).toHaveURL(new RegExp(`/manage/admin_unit/${adminUnitId}/events`));
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

    // The filter is collapsed until it is opened or the URL sets a filter.
    await expect(page.locator("#keyword")).toBeHidden();
    await page.locator("[data-test=toggle-filter]").click();
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

    // The calendar shows the dates of the same events; the fixture event starts now.
    await page.locator("[data-test=view-calendar]").click();
    await expect(page).toHaveURL(/view=calendar/);
    await expect(page.locator("#date_from")).toHaveCount(0);
    const date = page.locator("[data-test=calendar]").getByRole("button", { name: /Name/ }).first();
    await expect(date).toBeVisible();
    await screenshot(page, "events-calendar");
    await date.click();
    await expect(page.locator("[data-test=details]")).toBeVisible();
    await expect(page.locator("[data-test=edit]")).toHaveAttribute("href", /\/event\/\d+\/update/);
    await page.getByRole("button", { name: "Schließen" }).click();
    await page.locator("[data-test=view-list]").click();
    await expect(page).not.toHaveURL(/view=calendar/);
    await expect(page.getByRole("cell", { name: "Name" }).first()).toBeVisible();

    // The name opens the action menu, which leads to the (Jinja) edit page.
    await page.getByRole("button", { name: "Name" }).first().click();
    await page.locator("a.dropdown-item", { hasText: "Bearbeiten" }).click();
    await expect(page).toHaveURL(/\/event\/\d+\/update/);
  });
});
