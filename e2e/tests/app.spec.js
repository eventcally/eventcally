const { test, expect } = require("../fixtures");
const { screenshot } = require("../fixtures/helpers");
const { createAdminUnit } = require("../fixtures/flask");

async function createApp(page, adminUnitId, name = "Meine App") {
  await page.goto(`/manage/admin_unit/${adminUnitId}/app/create`);
  await page.locator("#client_name").fill(name);
  await page.locator("#permission-0").check();
  await page.locator("#submit").click();
  await expect(page).toHaveURL(/\/app\/\d+$/);
  return page.url().match(/\/app\/(\d+)$/)[1];
}

test.describe("App", () => {
  test("creates, shows and updates", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();

    await page.goto(`/manage/admin_unit/${adminUnitId}/app/create`);
    await page.locator("#client_name").fill("Meine App");
    await page.locator("#redirect_uris").fill("/oauth2-redirect.html");
    await page.locator("#scope-0").check();
    await page.locator("#permission-0").check();
    await page.locator("#webhook_url").fill("https://example.com/hook");
    await screenshot(page, "create");
    await page.locator("#submit").click();

    await expect(page).toHaveURL(/\/app\/\d+$/);
    await expect(page.locator(".breadcrumb")).toContainText("Meine App");
    await expect(page.locator("dl")).toContainText("https://example.com/hook");
    await screenshot(page, "read");

    await page.getByRole("button", { name: "Aktionen" }).click();
    await page.locator(".dropdown-menu.show .dropdown-item", { hasText: "Bearbeiten" }).click();
    await expect(page).toHaveURL(/\/app\/\d+\/update$/);
    await page.locator("#client_name").fill("Neuer Name");
    await screenshot(page, "update");
    await page.locator("#submit").click();
    await expect(page).toHaveURL(/\/app\/\d+$/);
    await expect(page.locator(".breadcrumb")).toContainText("Neuer Name");
  });

  test("lists and deletes in a modal", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    await createApp(page, adminUnitId);

    await page.goto(`/manage/admin_unit/${adminUnitId}/apps`);
    await expect(page.locator("tbody tr")).toHaveCount(1);
    await screenshot(page, "list");
    await page.locator("tbody tr .row-actions button").first().click();
    await page.locator(".dropdown-menu.show .dropdown-item", { hasText: "Löschen" }).click();
    await page.locator(".modal input").fill("Falscher Name");
    await page.locator(".modal button[type=submit]").click();
    await expect(page.locator(".modal .invalid-feedback")).toBeVisible();

    await page.locator(".modal input").fill("Meine App");
    await page.locator(".modal button[type=submit]").click();
    await expect(page.locator("tbody tr")).toHaveCount(0);
  });

  test("creates and deletes keys on the read page", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    await createApp(page, adminUnitId);

    const download = page.waitForEvent("download");
    await page.locator("[data-test=create-key]").click();
    expect((await download).suggestedFilename()).toBe("private_key.pem");
    await expect(page.locator("[data-test=pem-warning]")).toBeVisible();
    await expect(page.locator("[data-test=keys] tbody tr")).toHaveCount(1);
    await screenshot(page, "keys");

    await page.locator("[data-test=keys] tbody tr .row-actions button").click();
    await page.locator(".dropdown-menu.show .dropdown-item", { hasText: "Löschen" }).click();
    const kid = (await page.locator("[data-test=keys] tbody tr td").first().innerText()).trim();
    await page.locator(".modal input").last().fill(kid);
    await page.locator(".modal button[type=submit]").last().click();
    await expect(page.locator("[data-test=keys] tbody tr")).toHaveCount(0);
  });

  test("deletes from the read page and returns to the list", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    await createApp(page, adminUnitId);

    await page.getByRole("button", { name: "Aktionen" }).click();
    await page.locator(".dropdown-menu.show .dropdown-item", { hasText: "Löschen" }).click();
    await page.locator(".modal input").first().fill("Meine App");
    await page.locator(".modal button[type=submit]").first().click();

    await expect(page).toHaveURL(new RegExp(`/manage/admin_unit/${adminUnitId}/apps$`));
  });

  test("installs an app of another organization and uninstalls it", async ({ page, login }) => {
    await login();
    const ownerUnitId = createAdminUnit("test@test.de", "App Crew");
    const appId = await createApp(page, ownerUnitId);
    const adminUnitId = createAdminUnit("test@test.de", "Meine Crew");

    await page.goto(`/manage/admin_unit/${adminUnitId}/app_installations/install/${appId}`);
    await expect(page.getByText("Meine App").first()).toBeVisible();
    await screenshot(page, "install");
    await page.locator("#submit").click();
    await expect(page).toHaveURL(/\/app_installation\/\d+$/);
    await expect(page.locator("dl")).toContainText("Meine App");
    await screenshot(page, "installation");

    await page.goto(`/manage/admin_unit/${adminUnitId}/app_installations`);
    await expect(page.locator("tbody tr")).toHaveCount(1);
    await page.locator("tbody tr .row-actions button").first().click();
    await page.locator(".dropdown-menu.show .dropdown-item", { hasText: "Löschen" }).click();
    await page.locator(".modal .btn-danger").click();
    await expect(page.locator("tbody tr")).toHaveCount(0);
  });

  test("the removed pages are gone", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    const appId = await createApp(page, adminUnitId);

    for (const path of ["delete", "app_keys", "app_key/create"]) {
      const response = await page.request.get(`/manage/admin_unit/${adminUnitId}/app/${appId}/${path}`);
      expect(response.status()).toBe(404);
    }
  });
});
