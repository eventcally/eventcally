const { test, expect } = require("../fixtures");
const { screenshot } = require("../fixtures/helpers");
const { createAdminUnit, createUser, createAdminUnitMember } = require("../fixtures/flask");

test.describe("Admin Unit Member", () => {
  test("updates", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    createUser("new@test.de");
    const memberId = createAdminUnitMember(adminUnitId, "new@test.de");

    await page.goto(`/manage/admin_unit/${adminUnitId}/organization_member/${memberId}/update`);
    await screenshot(page, "update");
    await page.locator("#submit").click();
    await expect(page).toHaveURL(
      new RegExp(`/manage/admin_unit/${adminUnitId}/organization_members`)
    );
    await screenshot(page, "list");
  });

  test("deletes", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    createUser("new@test.de");
    const memberId = createAdminUnitMember(adminUnitId, "new@test.de");

    await page.goto(`/manage/admin_unit/${adminUnitId}/organization_member/${memberId}/delete`);
    await screenshot(page, "delete");
    await page.locator("#submit").click();
    await expect(page).toHaveURL(
      new RegExp(`/manage/admin_unit/${adminUnitId}/organization_members`)
    );
  });
});
