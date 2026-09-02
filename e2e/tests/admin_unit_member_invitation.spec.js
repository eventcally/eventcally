const { test, expect } = require("../fixtures");
const { screenshot } = require("../fixtures/helpers");
const { createAdminUnit, createAdminUnitMemberInvitation } = require("../fixtures/flask");

test.describe("Admin Unit Member Invitation", () => {
  test("creates", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    await page.goto(
      `/manage/admin_unit/${adminUnitId}/organization_member_invitation/create`
    );
    await page.locator("#email").fill("new@test.de");
    await screenshot(page, "create");
    await page.locator("#submit").click();
    await expect(page).toHaveURL(
      new RegExp(`/manage/admin_unit/${adminUnitId}/organization_member_invitations`)
    );
  });

  test("deletes", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    const invitationId = createAdminUnitMemberInvitation(adminUnitId);

    await page.goto(
      `/manage/admin_unit/${adminUnitId}/organization_member_invitation/${invitationId}/delete`
    );
    await screenshot(page, "delete");
    await page.locator("#submit").click();
    await expect(page).toHaveURL(
      new RegExp(`/manage/admin_unit/${adminUnitId}/organization_member_invitations`)
    );
  });

  test("reads", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    const invitationId = createAdminUnitMemberInvitation(adminUnitId, "test@test.de");

    await page.goto(`/invitations/${invitationId}`);
    await page.locator("#accept").click();
    await expect(page).toHaveURL(new RegExp(`/manage/admin_unit/${adminUnitId}/events`));
  });
});
