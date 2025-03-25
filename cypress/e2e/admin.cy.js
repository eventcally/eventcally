describe("Admin", () => {
  it("settings", () => {
    cy.createUser("admin@test.de", "password", true).then(function (userId) {
      cy.login("admin@test.de");
      cy.visit("/admin");
      cy.visit("/admin/settings");
      cy.get("#submit").click();
      cy.url().should("include", "/admin");
    });
  });

  it("admin units", () => {
    cy.createUser("admin@test.de", "password", true).then(function (userId) {
      cy.login("admin@test.de");
      cy.visit("/admin/organizations");

      cy.createAdminUnit().then(function (adminUnitId) {
        cy.visit("/admin/organization/" + adminUnitId + "/update");
        cy.get("#submit").click();
        cy.url().should("include", "/admin/organizations");
      });
    });
  });

  it("users", () => {
    cy.createUser("admin@test.de", "password", true).then(function (userId) {
      cy.login("admin@test.de");
      cy.visit("/admin/users");

      cy.visit("/admin/user/" + userId + "/update");
      cy.get("#submit").click();
      cy.url().should("include", "/admin/users");
    });
  });
});
