describe("Organization", () => {
  it("reads", () => {
    cy.createAdminUnit().then(function (adminUnitId) {
      cy.createEvent(adminUnitId).then(function (eventId) {
        cy.visit("/organization/" + adminUnitId);
        cy.screenshot("read");
      });
    });
  });
});
