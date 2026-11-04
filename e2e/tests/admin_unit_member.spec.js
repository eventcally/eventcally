const { test, expect } = require("../fixtures");
const { screenshot } = require("../fixtures/helpers");
const { createAdminUnit, createUser, createAdminUnitMember } = require("../fixtures/flask");

async function openRowActions(page, email) {
  const row = page.locator("tbody tr", { hasText: email });
  await row.locator(".row-actions button").first().click();
}

test.describe("Admin Unit Member", () => {
  test("lists", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    createUser("new@test.de");
    createAdminUnitMember(adminUnitId, "new@test.de");

    await page.goto(`/manage/admin_unit/${adminUnitId}/organization_members`);
    await expect(page.locator("tbody tr")).toHaveCount(2);
    await expect(page.locator(".b-overlay")).toHaveCount(0);
    await screenshot(page, "list");
  });

  test("updates the roles in a modal of the list", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    createUser("new@test.de");
    createAdminUnitMember(adminUnitId, "new@test.de");

    await page.goto(`/manage/admin_unit/${adminUnitId}/organization_members`);
    await expect(page.locator("tbody tr")).toHaveCount(2);
    await expect(page.locator(".b-overlay")).toHaveCount(0);
    await openRowActions(page, "new@test.de");
    await page.locator(".dropdown-menu.show .dropdown-item", { hasText: "Bearbeiten" }).click();
    await page.locator(".modal [data-test=roles] input").first().check();
    await screenshot(page, "update");
    await page.locator(".modal-footer").getByRole("button", { name: "Aktualisieren" }).click();

    await expect(page.getByText("Mitglied erfolgreich aktualisiert")).toBeVisible();
    await expect(
      page.locator("tbody tr", { hasText: "new@test.de" }).getByText("Administrator:in")
    ).toBeVisible();
  });

  test("removes a member in a modal of the list", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    createUser("new@test.de");
    createAdminUnitMember(adminUnitId, "new@test.de");

    await page.goto(`/manage/admin_unit/${adminUnitId}/organization_members`);
    await expect(page.locator("tbody tr")).toHaveCount(2);
    await expect(page.locator(".b-overlay")).toHaveCount(0);
    await openRowActions(page, "new@test.de");
    await page.locator(".dropdown-menu.show .dropdown-item", { hasText: "Löschen" }).click();
    await screenshot(page, "delete");
    await page.locator(".modal-footer").getByRole("button", { name: "Löschen" }).click();

    await expect(page.getByText("Mitglied erfolgreich gelöscht")).toBeVisible();
    await expect(page.locator("tbody tr")).toHaveCount(1);
  });

  test("links the own membership to the page that leaves the organization", async ({
    page,
    login,
  }) => {
    await login();
    const adminUnitId = createAdminUnit();

    await page.goto(`/manage/admin_unit/${adminUnitId}/organization_members`);
    await expect(page.locator("tbody tr")).toHaveCount(1);
    await expect(page.locator(".b-overlay")).toHaveCount(0);
    await openRowActions(page, "test@test.de");
    await expect(
      page.locator(".dropdown-menu.show .dropdown-item", { hasText: "Löschen" })
    ).toHaveAttribute("href", /\/user\/organization_member\/\d+\/delete/);
  });

  test("removes the old update and delete pages", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    createUser("new@test.de");
    const memberId = createAdminUnitMember(adminUnitId, "new@test.de");

    for (const action of ["update", "delete"]) {
      const response = await page.goto(
        `/manage/admin_unit/${adminUnitId}/organization_member/${memberId}/${action}`
      );
      expect(response.status()).toBe(404);
    }
  });
});
