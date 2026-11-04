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
    await page.goto(`/manage/admin_unit/${adminUnitId}/organization_invitation/create`);

    await page.locator("#email").fill("invited@test.de");
    await page.locator("#admin_unit_name").fill("Invited organization");
    await screenshot(page, "create");
    await page.locator("#submit").click();

    await expect(page).toHaveURL(/\/organization_invitations/);
    await expect(page.getByText("Organisationseinladung erfolgreich erstellt")).toBeVisible();
    await expect(page.locator("tbody tr", { hasText: "invited@test.de" })).toHaveCount(1);
    await screenshot(page, "list-filled");
  });

  test("updates", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    const invitationId = createAdminUnitOrganizationInvitation(adminUnitId);

    await page.goto(
      `/manage/admin_unit/${adminUnitId}/organization_invitation/${invitationId}/update`
    );
    await expect(page.locator("#admin_unit_name")).toBeVisible();
    await screenshot(page, "update");
    await page.locator("#submit").click();
    await expect(page).toHaveURL(/\/organization_invitations/);
    await expect(page.getByText("Organisationseinladung erfolgreich aktualisiert")).toBeVisible();
  });

  test("revokes in a modal of the list", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    createAdminUnitOrganizationInvitation(adminUnitId);

    await page.goto(`/manage/admin_unit/${adminUnitId}/organization_invitations`);
    await expect(page.locator("tbody tr")).toHaveCount(1);
    await expect(page.locator(".b-overlay")).toHaveCount(0);
    await page.locator("tbody .row-actions button").first().click();
    await page.locator(".dropdown-menu.show .dropdown-item", { hasText: "Löschen" }).click();
    await screenshot(page, "delete");
    await page.locator(".modal-footer").getByRole("button", { name: "Löschen" }).click();

    await expect(page.getByText("Organisationseinladung erfolgreich gelöscht")).toBeVisible();
    await expect(page.locator("tbody tr")).toHaveCount(0);
  });

  test("removes the old delete page", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    const invitationId = createAdminUnitOrganizationInvitation(adminUnitId);

    const response = await page.goto(
      `/manage/admin_unit/${adminUnitId}/organization_invitation/${invitationId}/delete`
    );
    expect(response.status()).toBe(404);
  });
});
