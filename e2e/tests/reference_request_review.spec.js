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
    await expect(page.locator("[data-test=decision]")).toBeVisible();
    await screenshot(page, "review");
    await page.locator("[data-test=reject]").click();
    const rejectionReason = page.locator("#rejection_reason");
    await rejectionReason.selectOption({ label: "Nicht relevant" });
    await expect(rejectionReason).toHaveValue("4");
    await screenshotElement(page.locator("[data-test=reject-modal]"), "reject");
    await page.locator("[data-test=reject-confirm]").click();
    await expect(page).toHaveURL(new RegExp(listUrl));
    await shouldContain(page.locator("div.alert"), "Empfehlungsanfrage erfolgreich aktualisiert");
    await shouldContain(page.locator("main .badge-pill"), "Abgelehnt");

    // Accept
    await page.goto(reviewUrl);
    await page.locator("[data-test=accept]").click();
    const rating = page.locator("#rating");
    await rating.selectOption({ label: "6" });
    await expect(rating).toHaveValue("60");
    await page.locator("#auto_verify").check();
    await screenshotElement(page.locator("[data-test=accept-modal]"), "accept");
    await page.locator("[data-test=accept-confirm]").click();
    await expect(page).toHaveURL(new RegExp(listUrl));
    await shouldContain(page.locator("div.alert"), "Empfehlung erfolgreich erstellt");
  });
});
