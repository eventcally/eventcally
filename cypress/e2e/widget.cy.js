describe("Widget", () => {
  it("event dates", () => {
    cy.createAdminUnit().then(function (adminUnitId) {
      cy.createEvent(adminUnitId).then(function (eventId) {
        cy.visit("/organizations/" + adminUnitId + "/widget/eventdates");
        cy.screenshotDatepicker("#date_from-user");
        cy.screenshot("eventdates");

        cy.get(".stretched-link")
          .invoke("attr", "href")
          .then((href) => {
            cy.visit(href);
            cy.screenshot("event-date");
          });
      });
    });
  });
});
