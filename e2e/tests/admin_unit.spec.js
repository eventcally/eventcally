const { test, expect } = require("../fixtures");
const { screenshot, shouldContain } = require("../fixtures/helpers");
const { createAdminUnit, createAdminUnitOrganizationInvitation } = require("../fixtures/flask");

test.describe("Admin Unit", () => {
  test("creates", async ({ page, login }) => {
    await login();
    await page.goto("/manage/organization/create");
    await page.locator("#name").fill("Second Crew");
    await page.locator("#location-postalCode").fill("38640");
    await page.locator("#location-city").fill("Goslar");
    await screenshot(page, "create");
    await page.locator("#submit").click();
    await expect(page).toHaveURL(/\/manage\/admin_unit\//);
  });

  test("creates from invitation", async ({ page, login }) => {
    await login();

    const adminUnitId = createAdminUnit();
    const invitationId = createAdminUnitOrganizationInvitation(adminUnitId, "test@test.de");
    await page.goto(`/manage/organization/create?invitation_id=${invitationId}`);

    await expect(page.locator("#name")).toHaveValue("Invited Organization");
    await expect(page.locator("#short_name")).toHaveValue("invitedorganization");
    await expect(page.locator("#short_name")).toHaveClass(/is-valid/);

    await page.locator("#location-postalCode").fill("38640");
    await page.locator("#location-city").fill("Goslar");
    await screenshot(page, "create");
    await page.locator("#submit").click();
    await expect(page).toHaveURL(/\/manage\/admin_unit\//);
  });

  test("updates", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    await page.goto(`/manage/admin_unit/${adminUnitId}/update`);
    await screenshot(page, "update");
    await page.locator("#submit").click();
    await expect(page).toHaveURL(new RegExp(`/manage/admin_unit/${adminUnitId}/update`));
    await shouldContain(page.locator("div.alert"), "Organisation erfolgreich aktualisiert");
  });

  test("widgets", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    await page.goto(`/manage/admin_unit/${adminUnitId}/widgets`);
    await screenshot(page, "widgets");
    await page.locator("#submit").click();
    await expect(page).toHaveURL(new RegExp(`/manage/admin_unit/${adminUnitId}/widgets`));
    await shouldContain(page.locator("div.alert"), "Einstellungen erfolgreich aktualisiert");
  });
});
