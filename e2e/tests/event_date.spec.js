const { test, expect } = require("../fixtures");
const { screenshot } = require("../fixtures/helpers");
const { createAdminUnit, createEvent } = require("../fixtures/flask");

test.describe("Event Date", () => {
  test("list, search and read", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    createEvent(adminUnitId);

    await page.goto("/eventdates");
    await expect(page.locator(".event-date-card").first()).toBeVisible();
    await page.locator("#toggle-search-btn").click();
    await screenshot(page, "search-form");
    await page.locator("#toggle-search-btn").click();

    await page.locator("#keyword").fill("Name");
    await page.locator("form button[type=submit]").click();
    await expect(page).toHaveURL(/keyword=Name/);

    await page.locator(".text-body").filter({ visible: true }).first().click();
    await expect(page).toHaveURL(/\/eventdate\/\d+/);
    await screenshot(page, "event-date");
  });

  test("applies legacy query arguments", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    createEvent(adminUnitId);

    await page.goto(`/eventdates?admin_unit_id=${adminUnitId}&keyword=Name`);

    await expect(page.locator("#keyword")).toHaveValue("Name");
    await expect(page.locator("#admin_unit_id")).toHaveValue("Meine Crew");
    await expect(page.locator(".event-date-card")).toHaveCount(1);
    await screenshot(page, "legacy-query");
  });

  test("shows the map", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    createEvent(adminUnitId);

    // The seeded place has no coordinates, so add some to the search result.
    await page.route("**/bff/public/event-dates?*", async (route) => {
      const response = await route.fetch();
      const body = await response.json();
      for (const item of body.items) {
        item.event.place = { name: item.event.place?.name ?? "Platz", latitude: 51.9, longitude: 10.4 };
      }
      await route.fulfill({ response, json: body });
    });

    await page.goto("/eventdates");
    await expect(page.locator(".event-date-card").first()).toBeVisible();
    await page.locator("#toggle-map-btn").click();

    await expect(page.locator(".event-dates-map")).toBeVisible();
    await expect(
      page.locator(".leaflet-marker-icon, .marker-cluster").first(),
    ).toBeVisible();
    await screenshot(page, "map");
  });

  test("references and unreferences an event", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    const otherAdminUnitId = createAdminUnit("test@test.de", "Other Crew");
    createEvent(adminUnitId);
    createEvent(otherAdminUnitId);

    await page.goto("/eventdates");
    // The event of the current organization is "own"; the other one can be referenced.
    await expect(page.locator('[data-test="reference-own"]')).toHaveCount(1);
    await screenshot(page, "references");

    await page.locator('[data-test="reference-none"]').click();
    await expect(page.locator('[data-test="reference-referenced"]')).toHaveCount(1);
    await expect(page.locator('[data-test="reference-none"]')).toHaveCount(0);

    await page.locator('[data-test="reference-referenced"]').click();
    await expect(page.locator('[data-test="reference-none"]')).toHaveCount(1);
  });
});
