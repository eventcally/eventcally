import "./commands";
import failOnConsoleError from 'cypress-fail-on-console-error';

failOnConsoleError();

beforeEach(() => {
  cy.setup();
});
