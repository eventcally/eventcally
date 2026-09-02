// ported from cypress/e2e/oauth2_client.cy.js
const { test, expect } = require("../fixtures");
const { screenshot } = require("../fixtures/helpers");
const { createUser, createOauth2Client } = require("../fixtures/flask");

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
  });

  test("updates", async ({ page, login }) => {
    const userId = createUser("new@test.de", "password", true);
    const result = createOauth2Client(userId);
    await login("new@test.de");

    await page.goto(`/user/oauth2_client/${result.oauth2_client_id}/update`);
    await screenshot(page, "update");
    await page.locator("#submit").click();
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
