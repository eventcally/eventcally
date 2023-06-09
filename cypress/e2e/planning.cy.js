describe("Planning", () => {
  it("search", () => {
    cy.login();
    cy.createAdminUnit().then(function (adminUnitId) {
      cy.createEvent(adminUnitId).then(function (eventId) {

        cy.visit("/planning");
        cy.wait(2000); // Wait for Vue to load
        cy.screenshot("result");
      });
    });
  });
});
