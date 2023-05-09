describe("Root", () => {
  it("simple", () => {
    cy.visit("/");
    cy.screenshot("home");

    cy.visit("/tos", {failOnStatusCode: false});
    cy.screenshot("tos");

    cy.visit("/legal_notice");
    cy.screenshot("legal_notice");

    cy.visit("/contact");
    cy.screenshot("contact");

    cy.visit("/privacy");
    cy.screenshot("privacy");

    cy.visit("/developer");
    cy.screenshot("developer");
  });

  it("example", () => {
    cy.createAdminUnit("test@test.de", "Goslar").then(function (adminUnitId) {
      cy.createEvent(adminUnitId).then(function (eventId) {
        cy.visit("/organizations");
        cy.screenshot("organizations");
      });
    });
  });
});
