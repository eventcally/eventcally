import "./commands";
import failOnConsoleError from "cypress-fail-on-console-error";
import failOnNetworkRequest from "cypress-fail-on-network-request";

const config = {
    requests: [
      { status: 200 },
      { status: 201 },
      { status: 204 },
    ],
};

failOnNetworkRequest(config);
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
