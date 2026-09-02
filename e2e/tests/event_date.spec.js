const { test } = require("../fixtures");
const { screenshot, screenshotDatepicker } = require("../fixtures/helpers");
const { createAdminUnit, createEvent } = require("../fixtures/flask");

test.describe("Event Date", () => {
  test("list, search and read", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    createEvent(adminUnitId);

    await page.goto("/eventdates");
    await page.locator("#toggle-search-btn").click();
    await screenshot(page, "search-form");
    await screenshotDatepicker(page, "#date_from-user");
    await page.locator("#toggle-search-btn").click();

    await page.locator(".text-body").filter({ visible: true }).first().click();
    await screenshot(page, "event-date");
  });
});
