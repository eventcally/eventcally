// ported from cypress/e2e/verification_request_review.cy.js
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
    await screenshot(page, "review");
    await page.locator(".decision-container .btn-danger").click();
    const rejectionReason = page.locator("#rejectFormModal select[name=rejection_reason]");
    await rejectionReason.selectOption({ label: "Nicht relevant" });
    await expect(rejectionReason).toHaveValue("6");
    await screenshotElement(page.locator("#rejectFormModal"), "reject");
    await page.locator("#rejectFormModal .btn-danger").click();
    await expect(page).toHaveURL(/\/incoming_organization_verification_requests/);
    await shouldContain(page.locator("div.alert"), "Verifizierungsanfrage erfolgreich aktualisiert");
    await shouldContain(page.locator("main .badge-pill"), "Abgelehnt");

    // Accept
    await page.goto(reviewUrl);
    await page.locator(".decision-container .btn-success").click();
    await page.locator("#auto_verify").locator("..").click();
    await screenshotElement(page.locator("#acceptFormModal"), "accept");
    await page.locator("#acceptFormModal .btn-success").click();
    await expect(page).toHaveURL(/\/incoming_organization_verification_requests/);
    await shouldContain(page.locator("div.alert"), "Organisation erfolgreich verifiziert");
  });
});
