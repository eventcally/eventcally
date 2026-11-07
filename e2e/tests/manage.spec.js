const { test, expect } = require("../fixtures");
const { screenshot } = require("../fixtures/helpers");
const {
  createAdminUnit,
  createAdminUnitOrganizationInvitation,
  createAdminUnitMemberInvitation,
  createEvent,
  createIncomingReference,
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

  test("Events with references", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    createEvent(adminUnitId);
    const referenceId = createIncomingReference(adminUnitId);

    await page.goto(`/manage/admin_unit/${adminUnitId}/events`);
    await expect(page.getByRole("cell", { name: "Name" })).toHaveCount(1);

    // The referenced event of the other organization joins the list on request.
    await page.locator("[data-test=toggle-filter]").click();
    await page.getByLabel("Empfehlungen einbeziehen").check();
    await page.getByRole("button", { name: "Veranstaltungen finden" }).click();
    await expect(page).toHaveURL(/include_references=1/);
    const marker = page.locator("[data-test=reference]");
    await expect(marker).toHaveCount(1);
    await expect(marker).toContainText("Empfehlung");
    await screenshot(page, "events-references");

    // A reference row offers the reference actions instead of editing the event.
    const row = page.locator("tr", { has: marker });
    await row.getByRole("button", { name: "Name" }).click();
    await expect(page.locator("a.dropdown-item", { hasText: "Empfehlung anzeigen" })).toBeVisible();
    await expect(page.locator("a.dropdown-item", { hasText: "Bearbeiten" })).toBeHidden();
    await page.keyboard.press("Escape");

    // The calendar shows both dates; the reference opens with its own actions.
    await page.locator("[data-test=view-calendar]").click();
    const dates = page.locator("[data-test=calendar]").getByRole("button", { name: /Name/ });
    await expect(dates).toHaveCount(2);
    await screenshot(page, "events-references-calendar");
    for (const index of [0, 1]) {
      await dates.nth(index).click();
      const details = page.locator("[data-test=details]");
      await expect(details).toBeVisible();
      if (await details.locator("[data-test=reference]").count()) {
        await expect(details.locator("[data-test=view-reference]")).toHaveAttribute(
          "href",
          `/manage/admin_unit/${adminUnitId}/incoming_event_reference/${referenceId}`,
        );
        await expect(details.locator("[data-test=edit]")).toHaveCount(0);
      }
      await page.getByRole("button", { name: "Schließen" }).click();
      await expect(details).toBeHidden();
    }
  });
});
