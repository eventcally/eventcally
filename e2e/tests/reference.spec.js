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

  test("lists and reads", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    const referenceId = createIncomingReference(adminUnitId);

    await page.goto(`/manage/admin_unit/${adminUnitId}/incoming_event_references`);
    await expect(page.locator("tbody tr")).toHaveCount(1);
    await expect(page.locator(".b-overlay")).toHaveCount(0);
    await screenshot(page, "incoming-list");

    await page.locator("tbody .row-actions button").first().click();
    await page.getByRole("menuitem", { name: "Anzeigen", exact: true }).click();
    await expect(page).toHaveURL(
      new RegExp(`/manage/admin_unit/${adminUnitId}/incoming_event_reference/${referenceId}$`)
    );
    await expect(page.locator("dl")).toContainText("5/10");
    await screenshot(page, "incoming");
  });

  test("updates the rating in a modal of the read page", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    const referenceId = createIncomingReference(adminUnitId);

    await page.goto(`/manage/admin_unit/${adminUnitId}/incoming_event_reference/${referenceId}`);
    await expect(page.locator("dl")).toBeVisible();
    await page.getByRole("button", { name: "Aktionen" }).click();
    await page.locator(".dropdown-menu.show .dropdown-item", { hasText: "Bearbeiten" }).click();
    await page.locator("#rating").selectOption("70");
    await screenshot(page, "update");
    await page.getByRole("button", { name: "Empfehlung aktualisieren" }).click();
    await expect(page.getByText("Eingehende Empfehlung erfolgreich aktualisiert")).toBeVisible();
    await expect(page.locator("dl")).toContainText("7/10");
  });

  test("deletes in a modal of the read page", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    const referenceId = createIncomingReference(adminUnitId);

    await page.goto(`/manage/admin_unit/${adminUnitId}/incoming_event_reference/${referenceId}`);
    await expect(page.locator("dl")).toBeVisible();
    await page.getByRole("button", { name: "Aktionen" }).click();
    await page.locator(".dropdown-menu.show .dropdown-item", { hasText: "Löschen" }).click();
    await screenshot(page, "delete");
    await page.getByRole("button", { name: "Empfehlung löschen" }).click();
    await expect(page).toHaveURL(
      new RegExp(`/manage/admin_unit/${adminUnitId}/incoming_event_references`)
    );
    await expect(page.getByText("Eingehende Empfehlung erfolgreich gelöscht")).toBeVisible();
  });

  test("deletes in a modal of the list", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    createIncomingReference(adminUnitId);

    await page.goto(`/manage/admin_unit/${adminUnitId}/incoming_event_references`);
    await expect(page.locator("tbody tr")).toHaveCount(1);
    await expect(page.locator(".b-overlay")).toHaveCount(0);
    await page.locator("tbody .row-actions button").first().click();
    await page.locator(".dropdown-menu.show .dropdown-item", { hasText: "Löschen" }).click();
    await page.getByRole("button", { name: "Empfehlung löschen" }).click();
    await expect(page.getByText("Eingehende Empfehlung erfolgreich gelöscht")).toBeVisible();
    await expect(page.locator("tbody tr")).toHaveCount(0);
  });
});
