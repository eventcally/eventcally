// ported from cypress/e2e/event_list.cy.js
const { test, expect } = require("../fixtures");
const { screenshot } = require("../fixtures/helpers");
const { createAdminUnit, createEventList } = require("../fixtures/flask");

test.describe("Event lists", () => {
  test("list", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    await page.goto(`/manage/admin_unit/${adminUnitId}/event-lists`);
    await screenshot(page, "list");
  });

  test("create", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    await page.goto(`/manage/admin_unit/${adminUnitId}/event-lists`);
    await page.goto(`/manage/admin_unit/${adminUnitId}/event-lists/create`);

    await page.locator("input[name=name]").fill("Sehr gute Liste");
    await screenshot(page, "create");
    await page.locator("button[type=submit]").click();

    await expect(page).not.toHaveURL(/\/create/);

    await expect(page.locator("button", { hasText: "Sehr" }).first()).toBeAttached();
    await screenshot(page, "list-filled");
  });

  test("read", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    const eventListId = createEventList(adminUnitId);
    await page.goto(`/manage/admin_unit/${adminUnitId}/event-lists/${eventListId}`);
    await screenshot(page, "read");
  });

  test("updates", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    const eventListId = createEventList(adminUnitId);
    await page.goto(`/manage/admin_unit/${adminUnitId}/event-lists`);
    await page.goto(`/manage/admin_unit/${adminUnitId}/event-lists/${eventListId}/update`);
    await screenshot(page, "update");
    await page.locator("button[type=submit]").click();
    await expect(page).not.toHaveURL(/\/update/);
  });

  test("deletes", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    createEventList(adminUnitId);
    await page.goto(`/manage/admin_unit/${adminUnitId}/event-lists`);

    await page.locator(".dropdown-toggle.btn-link").click();
    // Cypress' `li:last` resolved once; here the menu items appear as the
    // dropdown opens, so `.last()` can otherwise resolve to a partially rendered
    // menu and click the wrong entry. Waiting for visibility re-resolves it.
    const deleteItem = page.locator(".b-dropdown.show li").last();
    await expect(deleteItem).toBeVisible();
    await deleteItem.click();

    await expect(page.locator(".dropdown-toggle.btn-link")).toHaveCount(0);
  });
});
