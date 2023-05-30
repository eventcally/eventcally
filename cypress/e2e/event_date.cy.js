describe("Event Date", () => {
  it("list, search and read", () => {
    cy.login();
    cy.createAdminUnit().then(function (adminUnitId) {
      cy.createEvent(adminUnitId).then(function (eventId) {
        cy.visit("/eventdates");
        cy.get("#toggle-search-btn").click();
        cy.screenshot("search-form");
        cy.screenshotDatepicker("#date_from-user");
        cy.get("#toggle-search-btn").click();

        cy.get(".text-body:visible:first").click();
        cy.screenshot("event-date");
      });
    });
  });
});
