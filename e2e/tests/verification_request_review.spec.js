const { test, expect } = require("../fixtures");
const { screenshot, screenshotElement, shouldContain } = require("../fixtures/helpers");
const { createAdminUnit, createIncomingVerificationRequest } = require("../fixtures/flask");

test.describe("Verification request review", () => {
  test("reviews", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    const requestId = createIncomingVerificationRequest(adminUnitId);
    const reviewUrl = `/manage/admin_unit/${adminUnitId}/incoming_organization_verification_request/${requestId}/review`;

    // Reject
    await page.goto(reviewUrl);
    await expect(page.locator("[data-test=decision]")).toBeVisible();
    await screenshot(page, "review");
    await page.locator("[data-test=reject]").click();
    const rejectionReason = page.locator("#rejection_reason");
    await rejectionReason.selectOption({ label: "Nicht relevant" });
    await expect(rejectionReason).toHaveValue("6");
    await screenshotElement(page.locator("[data-test=reject-modal]"), "reject");
    await page.locator("[data-test=reject-confirm]").click();
    await expect(page).toHaveURL(/\/incoming_organization_verification_requests/);
    await shouldContain(page.locator("div.alert"), "Verifizierungsanfrage erfolgreich aktualisiert");
    await shouldContain(page.locator("main .badge-pill"), "Abgelehnt");

    // Accept
    await page.goto(reviewUrl);
    await page.locator("[data-test=accept]").click();
    await page.locator("#auto_verify").check();
    await screenshotElement(page.locator("[data-test=accept-modal]"), "accept");
    await page.locator("[data-test=accept-confirm]").click();
    await expect(page).toHaveURL(/\/incoming_organization_verification_requests/);
    await shouldContain(page.locator("div.alert"), "Organisation erfolgreich verifiziert");
  });
});
