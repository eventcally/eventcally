describe("Manage", () => {
  it("manage", () => {
    cy.login();
    cy.createAdminUnit().then(function (adminUnitId) {
      cy.createEvent(adminUnitId).then(function (eventId) {
        cy.visit("/manage/admin_unit/" + adminUnitId);
        cy.url().should(
          "include",
          "/manage/admin_unit/" + adminUnitId + "/events"
        );
        cy.screenshot("events")

        cy.get("#toggle-search-btn").click();
        cy.screenshot("search-form");
        cy.screenshotDatepicker("#date_from-user");
        cy.get("#toggle-search-btn").click();
      });
    });
  });
});
