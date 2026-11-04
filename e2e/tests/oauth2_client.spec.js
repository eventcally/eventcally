const { test, expect } = require("../fixtures");
const { screenshot } = require("../fixtures/helpers");
const { createAdminUnit, createUser, createOauth2Client } = require("../fixtures/flask");

test.describe("OAuth2 Client", () => {
  test("creates", async ({ page, login }) => {
    const userId = createUser("new@test.de", "password", true);
    createOauth2Client(userId);
    await login("new@test.de");

    await page.goto("/user/oauth2_client/create");
    await page.locator("#client_name").fill("Mein Client");
    await page.locator("#scope-0").check();
    await page.locator("#redirect_uris").fill("/oauth2-redirect.html");
    await screenshot(page, "create");
    await page.locator("#submit").click();
    await expect(page).toHaveURL(/\/user\/oauth2_client\/\d+$/);
  });

  test("updates", async ({ page, login }) => {
    const userId = createUser("new@test.de", "password", true);
    const result = createOauth2Client(userId);
    await login("new@test.de");

    await page.goto(`/user/oauth2_client/${result.oauth2_client_id}/update`);
    await screenshot(page, "update");
    await page.locator("#submit").click();
    await expect(page).toHaveURL(new RegExp(`/user/oauth2_client/${result.oauth2_client_id}$`));
  });

  test("deletes", async ({ page, login }) => {
    const userId = createUser("new@test.de", "password", true);
    const result = createOauth2Client(userId);
    await login("new@test.de");

    await page.goto(`/user/oauth2_client/${result.oauth2_client_id}/delete`);
    await page.locator("#name").fill("Mein Client");
    await screenshot(page, "delete");
    await page.locator("#submit").click();
    await expect(page).toHaveURL(/\/user\/oauth2_clients/);
  });

  test("lists and reads", async ({ page, login }) => {
    const userId = createUser("new@test.de", "password", true);
    const result = createOauth2Client(userId);
    await login("new@test.de");

    await page.goto("/user/oauth2_clients");
    await screenshot(page, "list");

    await page.goto(`/user/oauth2_client/${result.oauth2_client_id}`);
    await screenshot(page, "read");
  });
});

test.describe("Organization OAuth2 Client", () => {
  async function createClient(page, adminUnitId) {
    await page.goto(`/manage/admin_unit/${adminUnitId}/oauth2_client/create`);
    await page.locator("#client_name").fill("Mein Client");
    await page.locator("#scope-0").check();
    await page.locator("#redirect_uris").fill("/oauth2-redirect.html");
    await page.locator("#submit").click();
    await expect(page).toHaveURL(/\/oauth2_client\/\d+$/);
  }

  test("creates, reads and lists", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();

    await page.goto(`/manage/admin_unit/${adminUnitId}/oauth2_client/create`);
    await screenshot(page, "org-create");
    await createClient(page, adminUnitId);
    await expect(page.getByText("OAuth2 Client erfolgreich erstellt")).toBeVisible();
    await expect(page.locator("[data-test=oauth2-client-details]")).toContainText(
      "/oauth2-redirect.html"
    );
    await screenshot(page, "org-read");

    await page.goto(`/manage/admin_unit/${adminUnitId}/oauth2_clients`);
    await expect(page.locator("tbody tr")).toHaveCount(1);
    await expect(page.locator(".b-overlay")).toHaveCount(0);
    await screenshot(page, "org-list");
  });

  test("updates", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    await createClient(page, adminUnitId);

    await page.getByRole("button", { name: "Aktionen" }).click();
    await page.locator(".dropdown-menu.show .dropdown-item", { hasText: "Bearbeiten" }).click();
    await page.locator("#client_name").fill("Neuer Name");
    await screenshot(page, "org-update");
    await page.locator("#submit").click();

    await expect(page).toHaveURL(/\/oauth2_client\/\d+$/);
    await expect(page.getByText("OAuth2 Client erfolgreich aktualisiert")).toBeVisible();
    await expect(page.locator(".breadcrumb")).toContainText("Neuer Name");
  });

  test("deletes in a modal of the list", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    await createClient(page, adminUnitId);

    await page.goto(`/manage/admin_unit/${adminUnitId}/oauth2_clients`);
    await page.locator("tbody tr .row-actions button").first().click();
    await page.locator(".dropdown-menu.show .dropdown-item", { hasText: "Löschen" }).click();
    await page.locator(".modal input").fill("Falscher Name");
    await page.locator(".modal button[type=submit]").click();
    await expect(page.locator(".modal .invalid-feedback")).toBeVisible();
    await screenshot(page, "org-delete-mismatch");

    await page.locator(".modal input").fill("Mein Client");
    await page.locator(".modal button[type=submit]").click();
    await expect(page.getByText("OAuth2 Client erfolgreich gelöscht")).toBeVisible();
    await expect(page.locator("tbody tr")).toHaveCount(0);
  });

  test("the removed delete page is gone", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    await createClient(page, adminUnitId);

    const response = await page.goto(`${page.url()}/delete`);
    expect(response.status()).toBe(404);
  });
});
