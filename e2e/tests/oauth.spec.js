// ported from cypress/e2e/oauth.cy.js
const { test } = require("../fixtures");
const { authorize } = require("../fixtures/helpers");

test.describe("OAuth", () => {
  test("authorizes", async ({ page, login }) => {
    await authorize(page, login, true);
  });
});
