describe("OAuth2 Client", () => {
  it("creates", () => {
    cy.createUser("new@test.de", "password", true).then(function (userId) {
      cy.createOauth2Client(userId).then(function (result) {
        cy.login("new@test.de");

        cy.visit("/oauth2_client/create");
        cy.get("#client_name").type("Mein Client");
        cy.get("#scope-0").check();
        cy.get("#redirect_uris").type("/oauth2-redirect.html");
        cy.screenshot("create");
        cy.get("#submit").click();
      });
    });
  });

  it("updates", () => {
    cy.createUser("new@test.de", "password", true).then(function (userId) {
      cy.createOauth2Client(userId).then(function (result) {
        cy.login("new@test.de");

        cy.visit("/oauth2_client/" + result.oauth2_client_id + "/update");
        cy.screenshot("update");
        cy.get("#submit").click();
      });
    });
  });

  it("deletes", () => {
    cy.createUser("new@test.de", "password", true).then(function (userId) {
      cy.createOauth2Client(userId).then(function (result) {
        cy.login("new@test.de");

        cy.visit("/oauth2_client/" + result.oauth2_client_id + "/delete");
        cy.get("#name").type("Mein Client");
        cy.screenshot("delete");
        cy.get("#submit").click();
        cy.url().should("include", "/oauth2_clients");
      });
    });
  });

  it("lists and reads", () => {
    cy.createUser("new@test.de", "password", true).then(function (userId) {
      cy.createOauth2Client(userId).then(function (result) {
        cy.login("new@test.de");

        cy.visit("/oauth2_clients");
        cy.screenshot("list");

        cy.visit("/oauth2_client/" + result.oauth2_client_id);
        cy.screenshot("read");
      });
    });
  });
});
