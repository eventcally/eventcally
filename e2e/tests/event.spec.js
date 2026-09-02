const { test, expect } = require("../fixtures");
const { screenshot, select2, checkEventStartEnd, shouldContain } = require("../fixtures/helpers");
const { createAdminUnit, createEvent, createEventList } = require("../fixtures/flask");

test.describe("Event", () => {
  for (const { recurrence } of [{ recurrence: false }, { recurrence: true }]) {
    test(`creates event with recurrence=${recurrence}`, async ({ page, login }) => {
      await login();
      const adminUnitId = createAdminUnit();
      await page.goto(`/manage/admin_unit/${adminUnitId}/event/create`);

      await page.locator("#name").fill("Stadtfest");
      await checkEventStartEnd(page, false, recurrence, "date_definitions-0-");

      await page.locator("#add-date-defintion-btn").click();
      await checkEventStartEnd(page, false, recurrence, "date_definitions-1-");

      await page.locator("#event_place_choice-1").click();
      await page.locator("#new_event_place-location-city").fill("Goslar");
      await page.locator("#event_place_choice-0").click();
      await select2(page, "event_place", "Gos", "Goslar, 38640 Goslar");

      await page.locator("#organizer_choice-1").click();
      await page.locator("#new_organizer-location-city").fill("Goslar");
      await page.locator("#organizer_choice-0").click();
      await select2(page, "organizer", "Mei", "Meine Crew");

      await page.locator("#submit").click();
      await expect(page).toHaveURL(/\/actions/);
      await shouldContain(page.locator("div.alert"), "Veranstaltung erfolgreich veröffentlicht");

      await page.getByRole("link", { name: "Veranstaltung bearbeiten" }).click();
      await expect(page).toHaveURL(/\/update/);

      await checkEventStartEnd(page, true, recurrence, "date_definitions-0-");

      await page
        .locator('div[data-prefix="date_definitions-1-"] .remove-date-defintion-btn')
        .filter({ visible: true })
        .first()
        .click();

      await page.locator("#submit").click();
      await expect(page).toHaveURL(new RegExp(`/manage/admin_unit/${adminUnitId}/events`));
      await shouldContain(page.locator("div.alert"), "Veranstaltung erfolgreich aktualisiert");
    });
  }

  test("saves draft", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    await page.goto(`/manage/admin_unit/${adminUnitId}/event/create`);

    await page.locator("#name").fill("Stadtfest");
    await select2(page, "event_place", "Gos", "Goslar, 38640 Goslar");
    await select2(page, "organizer", "Mei", "Meine Crew");

    await page.locator("#submit_draft").click();
    await expect(page).toHaveURL(/\/actions/);
    await shouldContain(page.locator("div.alert"), "Entwurf erfolgreich gespeichert");

    await page.getByRole("link", { name: "Veranstaltung bearbeiten" }).click();
    await expect(page).toHaveURL(/\/update/);
    await expect(page.locator("#public_status")).toHaveValue("1");
    await page.locator("#submit").click();
    await expect(page).toHaveURL(new RegExp(`/manage/admin_unit/${adminUnitId}/events`));
    await shouldContain(page.locator("div.alert"), "Veranstaltung erfolgreich aktualisiert");
    await screenshot(page, "list");

    await page.goto(`/manage/admin_unit/${adminUnitId}/events`);
    await shouldContain(page.locator("main .badge-pill"), "Entwurf");
  });

  test("read and actions", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    const eventId = createEvent(adminUnitId);
    createEventList(adminUnitId);

    await page.goto(`/event/${eventId}`);
    await screenshot(page, "read");

    await page.goto(`/event/${eventId}/actions`);
    await screenshot(page, "actions");

    // Replaces `cy.wait(1000) // Wait for Vue to load`.
    const toListLink = page.getByRole("link", { name: "Zu Liste" });
    await expect(toListLink).toBeVisible();
    await toListLink.click();

    // A regex gives a case-sensitive match; `hasText` with a plain string would
    // be case-insensitive and match "ok" inside other words.
    const okButton = page.locator(".btn").filter({ hasText: /OK/ });
    await expect(okButton).toBeVisible();
    await screenshot(page, "lists");

    await okButton.click();
    await expect(okButton).toHaveCount(0);
  });

  test("report", async ({ page }) => {
    const adminUnitId = createAdminUnit();
    const eventId = createEvent(adminUnitId);
    await page.goto(`/event/${eventId}/report`);

    await page.locator("input[name=contactName]").fill("Firstname Lastname");
    await page.locator("input[name=contactEmail]").fill("firstname.lastname@test.de");
    await page
      .locator("textarea[name=message]")
      .fill("Die Veranstaltung kann leider nicht stattfinden.");
    await screenshot(page, "report");
    await page.locator("button[type=submit]").click();

    await expect(page.locator("button[type=submit]")).toHaveCount(0);
    await screenshot(page, "report-submitted");
  });

  test("deletes", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    const eventId = createEvent(adminUnitId);

    await page.goto(`/manage/admin_unit/${adminUnitId}/event/${eventId}/delete`);
    await screenshot(page, "delete");
    await page.locator("#submit").click();
    await expect(page).toHaveURL(new RegExp(`/manage/admin_unit/${adminUnitId}/events`));
  });
});
