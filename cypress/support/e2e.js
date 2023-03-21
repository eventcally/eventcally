import "./commands";
import failOnConsoleError from "cypress-fail-on-console-error";

failOnConsoleError();

before(() => {
  if (Cypress.browser.family === "chromium") {
    Cypress.automation("remote:debugger:protocol", {
      command: "Network.setCacheDisabled",
      params: { cacheDisabled: true },
    });
  }
});

beforeEach(() => {
  cy.setup();
});
