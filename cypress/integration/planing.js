describe("Planing", () => {
  it("search", () => {
    cy.createAdminUnit().then(function (adminUnitId) {
      cy.createEvent(adminUnitId).then(function (eventId) {

        cy.visit("/planing");
        cy.screenshot("search-form");
        cy.screenshotDatepicker("#date_from-user");
        cy.get('#submit').click();
        cy.screenshot("result");
      });
    });
  });
});
