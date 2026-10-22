const { test, expect } = require("../fixtures");
const { screenshot } = require("../fixtures/helpers");
const { createAdminUnit, createEvent } = require("../fixtures/flask");

const DATES_API = "/bff/manage/planning/event-dates";

test.describe("Planning", () => {
  test("search", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    createEvent(adminUnitId);

    await page.goto("/planning");
    // The calendar is the Vue 3 `manage` page (FullCalendar); the spinner is only rendered
    // while the event dates load, so this waits for the real end of loading.
    await expect(page.locator("[data-test=calendar]")).toBeVisible();
    await expect(page.locator("[data-test=loading]")).toBeHidden();
    await expect(page.locator("[data-test=calendar]").getByText("Name", { exact: true }).first()).toBeVisible();
    await screenshot(page, "result");

    // The details of a date: organization and a link to the public event date.
    await page.locator("[data-test=calendar]").getByText("Name", { exact: true }).first().click();
    const view = page.locator("[data-test=view]");
    await expect(view).toBeVisible();
    await expect(view).toHaveAttribute("href", /\/eventdate\/\d+$/);
    await screenshot(page, "popover");
    await page.getByRole("button", { name: "Schließen", exact: true }).click();
    await expect(view).toBeHidden();

    // Week and day views reload the dates for their range.
    for (const view of ["timeGridWeek", "timeGridDay"]) {
      const loaded = page.waitForResponse((r) => r.url().includes(DATES_API));
      await page.locator(`[data-test=view-${view}]`).click();
      expect((await loaded).ok()).toBe(true);
      await expect(page.locator("[data-test=loading]")).toBeHidden();
    }
    await page.locator("[data-test=view-dayGridMonth]").click();
    await expect(page.locator("[data-test=loading]")).toBeHidden();

    // The filter only takes effect on refresh.
    await page.locator("[data-test=filter]").click();
    await page.locator("[id^=planning-category-]").first().check();
    await screenshot(page, "filter");
    const filtered = page.waitForResponse(
      (r) => r.url().includes(DATES_API) && r.url().includes("category_id=")
    );
    await page.locator("[data-test=refresh]").click();
    expect((await filtered).ok()).toBe(true);
  });
});
