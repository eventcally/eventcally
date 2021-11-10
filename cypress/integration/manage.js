describe("Manage", () => {
  it("Organizations", () => {
    cy.login();
    cy.createAdminUnit().then(function (adminUnitId) {
      cy.createAdminUnitOrganizationInvitation(
        adminUnitId,
        "test@test.de"
      ).then(function (organizationInvitationId) {
        cy.createAdminUnitMemberInvitation(adminUnitId, "test@test.de").then(function (
          memberInvitationId
        ) {
          cy.visit("/manage/admin_units");
          cy.get("h1:contains('Einladungen')");
          cy.get("h1:contains('Organisationseinladungen')");
          cy.get("h1:contains('Organisationen')");
          cy.screenshot("organizations");
        });
      });
    });
  });

  it("Events", () => {
    cy.login();
    cy.createAdminUnit().then(function (adminUnitId) {
      cy.createEvent(adminUnitId).then(function (eventId) {
        cy.visit("/manage/admin_unit/" + adminUnitId);
        cy.url().should(
          "include",
          "/manage/admin_unit/" + adminUnitId + "/events"
        );
        cy.screenshot("events");

        cy.get("#toggle-search-btn").click();
        cy.screenshot("search-form");
        cy.screenshotDatepicker("#date_from-user");
        cy.get("#toggle-search-btn").click();
      });
    });
  });
});
