const { test, expect } = require("../fixtures");
const { screenshot, select2 } = require("../fixtures/helpers");
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

    await select2(page, "target_admin_unit", "Oth", "Other Crew");
    await screenshot(page, "create");
    await page.locator("input[type=submit]").click();

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
    await page.locator("input[type=submit]").click();
    await expect(page).not.toHaveURL(/\/update/);
  });

  test("deletes", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    const relationId = createAdminUnitRelation(adminUnitId);

    await page.goto(
      `/manage/admin_unit/${adminUnitId}/outgoing_organization_relation/${relationId}/delete`
    );
    await screenshot(page, "update");
    await page.locator("input[type=submit]").click();
    await expect(page).not.toHaveURL(/\/update/);
  });
});
