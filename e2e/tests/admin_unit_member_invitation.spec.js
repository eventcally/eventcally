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
    await expect(page.getByText("Mitgliedschaftseinladung erfolgreich erstellt")).toBeVisible();
    await expect(page.locator("tbody tr", { hasText: "new@test.de" })).toHaveCount(1);
  });

  test("updates the roles in a modal of the list", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    createAdminUnitMemberInvitation(adminUnitId, "new@test.de");

    await page.goto(`/manage/admin_unit/${adminUnitId}/organization_member_invitations`);
    await expect(page.locator("tbody tr")).toHaveCount(1);
    await expect(page.locator(".b-overlay")).toHaveCount(0);
    await page.locator("tbody .row-actions button").first().click();
    await page.locator(".dropdown-menu.show .dropdown-item", { hasText: "Bearbeiten" }).click();
    await screenshot(page, "update");
    await page.locator(".modal-footer").getByRole("button", { name: "Aktualisieren" }).click();

    await expect(page.getByText("Mitgliedschaftseinladung erfolgreich aktualisiert")).toBeVisible();
  });

  test("revokes in a modal of the list", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    createAdminUnitMemberInvitation(adminUnitId);

    await page.goto(`/manage/admin_unit/${adminUnitId}/organization_member_invitations`);
    await expect(page.locator("tbody tr")).toHaveCount(1);
    await expect(page.locator(".b-overlay")).toHaveCount(0);
    await page.locator("tbody .row-actions button").first().click();
    await page.locator(".dropdown-menu.show .dropdown-item", { hasText: "Löschen" }).click();
    await screenshot(page, "delete");
    await page.locator(".modal-footer").getByRole("button", { name: "Löschen" }).click();

    await expect(page.getByText("Mitgliedschaftseinladung erfolgreich gelöscht")).toBeVisible();
    await expect(page.locator("tbody tr")).toHaveCount(0);
  });

  test("removes the old update and delete pages", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    const invitationId = createAdminUnitMemberInvitation(adminUnitId);

    for (const action of ["update", "delete"]) {
      const response = await page.goto(
        `/manage/admin_unit/${adminUnitId}/organization_member_invitation/${invitationId}/${action}`
      );
      expect(response.status()).toBe(404);
    }
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
