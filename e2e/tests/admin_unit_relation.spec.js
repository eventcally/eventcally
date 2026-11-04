const { test, expect } = require("../fixtures");
const { screenshot, typeahead } = require("../fixtures/helpers");
const { createAdminUnit, createAdminUnitRelation } = require("../fixtures/flask");

test.describe("Admin unit relations", () => {
  test("list", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    createAdminUnit("test@test.de", "Other Crew");
    await page.goto(`/manage/admin_unit/${adminUnitId}/outgoing_organization_relations`);
    await screenshot(page, "list");
  });

  test("create", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    createAdminUnit("test@test.de", "Other Crew");

    await page.goto(`/manage/admin_unit/${adminUnitId}/outgoing_organization_relation/create`);

    await typeahead(page, "target_admin_unit", "Oth", "Other Crew");
    await screenshot(page, "create");
    await page.locator("#submit").click();

    await expect(page).not.toHaveURL(/\/create/);
  });

  test("updates", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    const relationId = createAdminUnitRelation(adminUnitId);

    await page.goto(
      `/manage/admin_unit/${adminUnitId}/outgoing_organization_relation/${relationId}/update`
    );
    await screenshot(page, "update");
    await page.locator("#submit").click();
    await expect(page).not.toHaveURL(/\/update/);
  });

  test("lists with the dropdown and filters", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    createAdminUnitRelation(adminUnitId);

    await page.goto(`/manage/admin_unit/${adminUnitId}/outgoing_organization_relations`);
    await expect(page.locator("tbody tr")).toHaveCount(1);
    await expect(page.locator(".b-overlay")).toHaveCount(0);

    await page.getByRole("button", { name: "Filter" }).click();
    await page.locator("#verify-yes").check();
    await page.getByRole("button", { name: "Aktualisieren" }).click();
    await expect(page).toHaveURL(/verify=1/);
    await expect(page.locator("tbody tr")).toHaveCount(0);
  });

  test("deletes in a modal of the list", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    createAdminUnitRelation(adminUnitId);

    await page.goto(`/manage/admin_unit/${adminUnitId}/outgoing_organization_relations`);
    await expect(page.locator("tbody tr")).toHaveCount(1);
    await expect(page.locator(".b-overlay")).toHaveCount(0);
    await page.locator("tbody .row-actions button").first().click();
    await page.locator(".dropdown-menu.show .dropdown-item", { hasText: "Löschen" }).click();
    await screenshot(page, "delete");
    await page.locator(".modal-footer").getByRole("button", { name: "Löschen" }).click();
    await expect(
      page.getByText("Ausgehende Organisationsbeziehung erfolgreich gelöscht")
    ).toBeVisible();
    await expect(page.locator("tbody tr")).toHaveCount(0);
  });

  test("removes the old delete page", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    const relationId = createAdminUnitRelation(adminUnitId);

    const response = await page.goto(
      `/manage/admin_unit/${adminUnitId}/outgoing_organization_relation/${relationId}/delete`
    );
    expect(response.status()).toBe(404);
  });
});
