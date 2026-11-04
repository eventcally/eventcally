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

  test("creates through the dialog of the list and withdraws on the read page", async ({
    page,
    login,
  }) => {
    await login();
    createAdminUnit();
    const otherAdminUnitId = createAdminUnit("test@test.de", "Other Crew", false);

    // An unverified organization without a request is led to the dialog.
    await page.goto(`/manage/admin_unit/${otherAdminUnitId}/outgoing_organization_verification_requests`);
    const verifier = page.locator("[data-test=verifier-card]", { hasText: "Meine Crew" });
    await expect(verifier).toBeVisible();
    await screenshot(page, "create-select");
    await verifier.locator("[data-test=verifier-select]").click();
    await screenshot(page, "create");
    await page.locator("[data-test=verification-submit]").click();

    await expect(page.getByText("Verifizierungsanfrage erfolgreich erstellt")).toBeVisible();
    await expect(page.locator("tbody tr")).toHaveCount(1);
    await screenshot(page, "outgoing");

    // Status
    await page.locator("tbody .row-actions button").first().click();
    await page.getByRole("menuitem", { name: "Anzeigen", exact: true }).click();
    await expect(page).toHaveURL(/\/outgoing_organization_verification_request\//);
    await expect(page.locator("dl")).toContainText("Meine Crew");
    await screenshot(page, "status");

    await page.getByRole("button", { name: "Aktionen" }).click();
    await page.locator(".dropdown-menu.show .dropdown-item", { hasText: "Löschen" }).click();
    await page.locator(".modal-footer").getByRole("button", { name: "Löschen" }).click();
    await expect(page).toHaveURL(/\/outgoing_organization_verification_requests/);
    await expect(page.getByText("Verifizierungsanfrage erfolgreich gelöscht")).toBeVisible();
  });

  test("removes the old selection and withdraw pages", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();

    const response = await page.goto(
      `/manage/admin_unit/${adminUnitId}/verification_requests/outgoing/create/select`
    );
    expect(response.status()).toBe(404);
  });
});
