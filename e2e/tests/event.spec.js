const { test, expect } = require("../fixtures");
const {
  screenshot,
  typeahead,
  checkVueEventStartEnd,
  shouldContain,
} = require("../fixtures/helpers");
const { createAdminUnit, createEvent, createEventOrganizer } = require("../fixtures/flask");

test.describe("Event", () => {
  for (const { recurrence } of [{ recurrence: false }, { recurrence: true }]) {
    test(`creates event with recurrence=${recurrence}`, async ({ page, login }) => {
      await login();
      const adminUnitId = createAdminUnit();
      await page.goto(`/manage/admin_unit/${adminUnitId}/event/create`);

      await page.locator("#name").fill("Stadtfest");
      await checkVueEventStartEnd(page, 0, recurrence);

      await page.locator("#add-date-definition-btn").click();
      await checkVueEventStartEnd(page, 1, recurrence);

      // A new place from the modal is selected right away.
      await page.locator("#event_place-new-btn").click();
      const placeModal = page.locator("[data-test=event-place-create-modal]");
      await placeModal.locator("#new_event_place-name").fill("Neuer Ort");
      await placeModal.locator("#location-postalCode").fill("38640");
      await placeModal.locator("#location-city").fill("Goslar");
      await placeModal.locator(".modal-footer .btn-primary").click();
      await expect(placeModal).toBeHidden();
      await expect(page.locator("#event_place")).toHaveValue("Neuer Ort, 38640 Goslar");

      await typeahead(page, "organizer", "Mei", "Meine Crew");

      await page.locator("#submit").click();
      await expect(page).toHaveURL(/\/actions/);
      await shouldContain(page.locator("div.alert"), "Veranstaltung erfolgreich veröffentlicht");
      // The inline place create flashed nothing.
      await expect(page.locator("div.alert", { hasText: "Ort erfolgreich erstellt" })).toHaveCount(0);

      await page.getByRole("link", { name: "Veranstaltung bearbeiten" }).click();
      await expect(page).toHaveURL(/\/update/);
      await expect(page.locator("#name")).toHaveValue("Stadtfest");
      await expect(page.locator("#event_place")).toHaveValue("Neuer Ort, 38640 Goslar");

      const summary = page.locator("[data-test=date_definitions-0-recurrence-summary]");
      if (recurrence) {
        await expect(summary).toContainText("Woche");
      } else {
        await expect(summary).toBeHidden();
      }

      await page.locator("[data-test=date_definitions-1-remove]").click();
      await expect(page.locator("#date_definitions-1-start")).toHaveCount(0);

      await page.locator("#submit").click();
      await expect(page).toHaveURL(new RegExp(`/manage/admin_unit/${adminUnitId}/events`));
      await shouldContain(page.locator("div.alert"), "Veranstaltung erfolgreich aktualisiert");
    });
  }

  test("creates organizer inline", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    await page.goto(`/manage/admin_unit/${adminUnitId}/event/create`);

    await page.locator("#organizer-new-btn").click();
    const modal = page.locator("[data-test=event-organizer-create-modal]");
    await modal.locator("#new_organizer-name").fill("Neuer Veranstalter");
    await modal.locator(".modal-footer .btn-primary").click();
    await expect(modal).toBeHidden();
    await expect(page.locator("#organizer")).toHaveValue("Neuer Veranstalter");
  });

  test("updates co-organizers", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    const eventId = createEvent(adminUnitId);
    createEventOrganizer(adminUnitId, "Mein Veranstalter");
    const updateUrl = `/manage/admin_unit/${adminUnitId}/event/${eventId}/update`;

    const coOrganizerChips = page
      .locator(".multi-typeahead", { has: page.locator("#co_organizers") })
      .locator("[data-test=chip]");

    await page.goto(updateUrl);
    await page.locator("#co_organizers").pressSequentially("Mein V");
    await page.locator("[data-test=option]", { hasText: "Mein Veranstalter" }).click();
    await expect(coOrganizerChips).toContainText("Mein Veranstalter");
    await page.locator("#submit").click();
    await expect(page).toHaveURL(new RegExp(`/manage/admin_unit/${adminUnitId}/events`));
    await shouldContain(page.locator("div.alert"), "Veranstaltung erfolgreich aktualisiert");

    await page.goto(updateUrl);
    await expect(coOrganizerChips).toContainText("Mein Veranstalter");
  });

  test("saves draft", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    await page.goto(`/manage/admin_unit/${adminUnitId}/event/create`);

    await page.locator("#name").fill("Stadtfest");
    await typeahead(page, "event_place", "Gos", "Goslar, 38640 Goslar");
    await typeahead(page, "organizer", "Mei", "Meine Crew");

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
    await shouldContain(page.locator("main .badge"), "Entwurf");
  });

  test("read and actions", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    const eventId = createEvent(adminUnitId);

    await page.goto(`/event/${eventId}`);
    await screenshot(page, "read");

    await page.goto(`/event/${eventId}/actions`);
    await screenshot(page, "actions");
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
