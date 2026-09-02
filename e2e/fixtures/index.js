// Extended Playwright `test` object for the e2e suite.
//
// Ported from cypress/support/e2e.js (global hooks) and
// cypress/support/commands.js:199-209 (`login`).
const base = require("@playwright/test");
const { resetAndSeed, createUser } = require("./flask");

const expect = base.expect;

const test = base.test.extend({
  // SOURCE: cypress/support/e2e.js:18-20 — the global `beforeEach(cy.setup)`.
  // Truncates and re-seeds the database, then recreates the default user.
  // This is why playwright.config.js pins `workers: 1`.
  setup: [
    async ({}, use) => {
      resetAndSeed();
      createUser();
      await use();
    },
    { auto: true },
  ],

  // SOURCE: cypress/support/e2e.js:6-14 — the `Network.setCacheDisabled` CDP call.
  // Kept for parity with the Cypress suite, so a stale HTTP response can never
  // make a ported spec disagree with its twin. The related back/forward-cache
  // problem is handled by a launch argument in playwright.config.js — bfcache is
  // not the HTTP cache and this call does not affect it.
  disableCache: [
    async ({ context, page }, use) => {
      const client = await context.newCDPSession(page);
      // Network.enable is required before setCacheDisabled has any effect.
      await client.send("Network.enable");
      await client.send("Network.setCacheDisabled", { cacheDisabled: true });
      await use();
    },
    { auto: true },
  ],

  // Cypress auto-accepts `window.confirm` / `window.alert`; Playwright's default
  // is the opposite — it dismisses every dialog, so a `confirm()` returns false.
  // Without this, event_list "deletes" silently does nothing: the delete menu
  // item is guarded by `confirm()` (project/static/vue/event-lists/list.vue.js:125).
  acceptDialogs: [
    async ({ page }, use) => {
      page.on("dialog", (dialog) => dialog.accept());
      await use();
    },
    { auto: true },
  ],

  // SOURCE: cypress/support/e2e.js:2-4 — `failOnConsoleError()`.
  // Strict by default. Every entry in IGNORED_CONSOLE_ERRORS must be justified.
  failOnConsoleError: [
    async ({ page }, use) => {
      const errors = [];

      page.on("console", (msg) => {
        if (msg.type() === "error" && !isIgnoredConsoleError(msg.text())) {
          errors.push(msg.text());
        }
      });
      page.on("pageerror", (error) => {
        errors.push(error.message);
      });

      await use();

      expect(errors, `Console errors:\n${errors.join("\n")}`).toEqual([]);
    },
    { auto: true },
  ],

  // SOURCE: cypress/support/commands.js:199-209
  login: async ({ page, context }, use) => {
    await use(async (email = "test@test.de", password = "password", redirectUrl = "/manage") => {
      await page.goto("/login");
      await page.locator("#email").fill(email);
      await page.locator("#password").fill(password);
      await page.locator("#submit").click();
      await expect(page).toHaveURL(new RegExp(escapeRegExp(redirectUrl)));

      const cookies = await context.cookies();
      expect(cookies.find((cookie) => cookie.name === "session")).toBeTruthy();
    });
  },
});

// cypress-fail-on-console-error patches the page's `console.error`, so it only
// ever saw errors logged by page scripts. Playwright's `page.on("console")` also
// receives messages Chromium itself emits, which the Cypress suite never failed
// on. Ignoring them keeps the two guards equivalent rather than making the
// Playwright suite stricter than the one it replaces.
//
// - "Failed to load resource": Chromium's own log line for any non-2xx or failed
//   request. root.spec.js visits /tos, which legitimately 404s — that is why the
//   Cypress spec passes `{failOnStatusCode: false}`.
const IGNORED_CONSOLE_ERRORS = [/^Failed to load resource: /];

function isIgnoredConsoleError(text) {
  return IGNORED_CONSOLE_ERRORS.some((pattern) => pattern.test(text));
}

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

module.exports = { test, expect };
