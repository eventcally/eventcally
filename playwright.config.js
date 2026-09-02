// @ts-check
const { defineConfig, devices } = require("@playwright/test");

/**
 * Playwright configuration for the e2e suite.
 *
 * Runs alongside the Cypress suite in `cypress/` during the migration overlap.
 * Never run both against the same app/database at the same time: each test
 * truncates every table (see the `setup` fixture in `e2e/fixtures/index.js`).
 */
module.exports = defineConfig({
  testDir: "./e2e/tests",

  // MANDATORY: every test starts with `flask test reset --seed`, which truncates
  // every table in the database. A second worker sharing that database would wipe
  // another test's data mid-flight. Parallelism comes from `--shard` across CI
  // jobs (each with its own postgres service), never from workers.
  // Do not raise this without first giving each worker its own database.
  workers: 1,
  fullyParallel: false,

  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["html"], ["github"]] : "list",

  use: {
    baseURL: process.env.BASE_URL || "http://127.0.0.1:5000",
    trace: "on-first-retry",
    screenshot: "only-on-failure",

    // The app picks its language from Accept-Language (project/i10n.py:24-29),
    // so the browser locale decides whether the UI is German or English. Cypress
    // inherited de-DE from the machine / the workflow's LANG=de_DE.UTF-8;
    // Playwright's Chromium would default to en-US and every German assertion
    // in the suite would fail. This is as load-bearing as the viewport.
    locale: "de-DE",
  },

  projects: [
    {
      name: "desktop",
      use: {
        ...devices["Desktop Chrome"],
        // Cypress' default viewport, mirrored so responsive assertions match.
        viewport: { width: 1000, height: 660 },
      },
    },
    {
      name: "mobile",
      use: {
        ...devices["Desktop Chrome"],
        // SOURCE: cypress/config/mobile.config.js:4-5
        viewport: { width: 375, height: 667 },
      },
    },
  ],
});
