const { test } = require("../fixtures");
const { screenshot, screenshotDatepicker } = require("../fixtures/helpers");
const { createAdminUnit, createEvent } = require("../fixtures/flask");

test.describe("Widget", () => {
  test("event dates", async ({ page }) => {
    const adminUnitId = createAdminUnit();
    createEvent(adminUnitId);

    await page.goto(`/organizations/${adminUnitId}/widget/eventdates`);
    await screenshotDatepicker(page, "#date_from-user");
    await screenshot(page, "eventdates");

    // jQuery's .attr() reads the first match, so mirror that with .first().
    const href = await page.locator(".stretched-link").first().getAttribute("href");
    await page.goto(href);
    await screenshot(page, "event-date");
  });
});
