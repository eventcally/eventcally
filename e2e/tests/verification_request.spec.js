const { test, expect } = require("../fixtures");
const { screenshot } = require("../fixtures/helpers");
const { createAdminUnit, createIncomingVerificationRequest } = require("../fixtures/flask");

test.describe("Verification request", () => {
  test("lists", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    createIncomingVerificationRequest(adminUnitId);

    await page.goto(
      `/manage/admin_unit/${adminUnitId}/incoming_organization_verification_requests`
    );
    await screenshot(page, "incoming");
  });

  test("creates", async ({ page, login }) => {
    await login();
    createAdminUnit();
    const otherAdminUnitId = createAdminUnit("test@test.de", "Other Crew", false);

    await page.goto(
      `/manage/admin_unit/${otherAdminUnitId}/verification_requests/outgoing/create/select`
    );
    await screenshot(page, "create-select");
    await page.locator(".btn-primary").first().click();

    await expect(page).toHaveURL(/\/verification_requests\/outgoing\/create\/target/);
    await screenshot(page, "create");
    await page.locator("#submit").click();

    await expect(page).toHaveURL(/\/outgoing_organization_verification_requests/);
    await screenshot(page, "outgoing");

    // Status
    await page.locator(".dropdown-toggle.btn-link").click();
    // `hasText` is case-insensitive and would also match "Veranstaltungen
    // anzeigen", so this needs an exact, case-sensitive match.
    await page.getByRole("link", { name: "Anzeigen", exact: true }).click({ force: true });
    await expect(page).toHaveURL(/\/outgoing_organization_verification_request\//);
    await screenshot(page, "status");
  });
});
