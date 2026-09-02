const { test, expect } = require("../fixtures");
const { screenshot } = require("../fixtures/helpers");
const { createAdminUnit, createAdminUnitOrganizationInvitation } = require("../fixtures/flask");

test.describe("Admin unit organization invitations", () => {
  test("list", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    await page.goto(`/manage/admin_unit/${adminUnitId}/organization_invitations`);
    await screenshot(page, "list");
  });

  test("create", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    await page.goto(`/manage/admin_unit/${adminUnitId}/organization_invitations`);
    await page.goto(`/manage/admin_unit/${adminUnitId}/organization_invitation/create`);

    await page.locator("input[name=email]").fill("invited@test.de");
    await page.locator("input[name=admin_unit_name]").fill("Invited organization");
    await screenshot(page, "create");
    await page.locator("input[type=submit]").click();

    await expect(page).not.toHaveURL(/\/create/);

    await expect(
      page.locator("button", { hasText: "invited@test.de" }).first()
    ).toBeAttached();
    await screenshot(page, "list-filled");
  });

  test("updates", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    const invitationId = createAdminUnitOrganizationInvitation(adminUnitId);

    await page.goto(`/manage/admin_unit/${adminUnitId}/organization_invitations`);
    await page.goto(
      `/manage/admin_unit/${adminUnitId}/organization_invitation/${invitationId}/update`
    );
    await screenshot(page, "update");
    await page.locator("input[type=submit]").click();
    await expect(page).not.toHaveURL(/\/update/);
  });

  test("deletes", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    const invitationId = createAdminUnitOrganizationInvitation(adminUnitId);

    await page.goto(`/manage/admin_unit/${adminUnitId}/organization_invitations`);
    await page.goto(
      `/manage/admin_unit/${adminUnitId}/organization_invitation/${invitationId}/delete`
    );
    await screenshot(page, "delete");
    await page.locator("input[type=submit]").click();
    await expect(page).not.toHaveURL(/\/delete/);
  });
});
