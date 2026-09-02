// Extended Playwright `test` object for the e2e suite.
//
// Global hooks (database reset, console-error guard, dialogs) and `login`.
const base = require("@playwright/test");
const { resetAndSeed, createUser } = require("./flask");

const expect = base.expect;

const test = base.test.extend({
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

  // Disables the HTTP cache, so a stale response can never make a spec assert
  // against pre-mutation data after a `history.back()`.
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

  // Playwright dismisses every dialog by default, so a `confirm()` returns false.
  // Without this, event_list "deletes" silently does nothing: the delete menu item
  // is guarded by `confirm()` (project/static/vue/event-lists/list.vue.js:125).
  acceptDialogs: [
    async ({ page }, use) => {
      page.on("dialog", (dialog) => dialog.accept());
      await use();
    },
    { auto: true },
  ],

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

// `page.on("console")` receives messages Chromium itself emits, not just errors
// logged by page scripts, so the guard needs a narrow allow-list.
//
// - "Failed to load resource": Chromium's own log line for any non-2xx or failed
//   request. root.spec.js visits /tos, which legitimately 404s.
const IGNORED_CONSOLE_ERRORS = [/^Failed to load resource: /];

function isIgnoredConsoleError(text) {
  return IGNORED_CONSOLE_ERRORS.some((pattern) => pattern.test(text));
}

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

module.exports = { test, expect };
