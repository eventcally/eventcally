// ported from cypress/e2e/reference_request_review.cy.js
const { test, expect } = require("../fixtures");
const { screenshot, screenshotElement, shouldContain } = require("../fixtures/helpers");
const { createAdminUnit, createIncomingReferenceRequest } = require("../fixtures/flask");

test.describe("Reference request review", () => {
  test("reviews", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    const referenceRequestId = createIncomingReferenceRequest(adminUnitId);
    const reviewUrl = `/manage/admin_unit/${adminUnitId}/incoming_event_reference_request/${referenceRequestId}/review`;
    const listUrl = `/manage/admin_unit/${adminUnitId}/incoming_event_reference_requests`;

    // Reject
    await page.goto(reviewUrl);
    await screenshot(page, "review");
    await page.locator(".decision-container .btn-danger").click();
    const rejectionReason = page.locator("#rejectFormModal select[name=rejection_reason]");
    await rejectionReason.selectOption({ label: "Nicht relevant" });
    await expect(rejectionReason).toHaveValue("4");
    await screenshotElement(page.locator("#rejectFormModal"), "reject");
    await page.locator("#rejectFormModal .btn-danger").click();
    await expect(page).toHaveURL(new RegExp(listUrl));
    await shouldContain(page.locator("div.alert"), "Empfehlungsanfrage erfolgreich aktualisiert");
    await shouldContain(page.locator("main .badge-pill"), "Abgelehnt");

    // Accept
    await page.goto(reviewUrl);
    await page.locator(".decision-container .btn-success").click();
    const rating = page.locator("#acceptFormModal select[name=rating]");
    await rating.selectOption({ label: "6" });
    await expect(rating).toHaveValue("60");
    await page.locator("#auto_verify").locator("..").click();
    await screenshotElement(page.locator("#acceptFormModal"), "accept");
    await page.locator("#acceptFormModal .btn-success").click();
    await expect(page).toHaveURL(new RegExp(listUrl));
    await shouldContain(page.locator("div.alert"), "Empfehlung erfolgreich erstellt");
  });
});
