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
        cy.createEventList(adminUnitId).then(function (eventListId) {
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

          cy.get('.dropdown-toggle.btn-link').click();
          cy.get('a:contains(Zu Liste)').click({force: true});
          cy.get(".btn:contains(OK)").should("be.visible");
          cy.screenshot("lists");

          cy.get(".btn:contains(OK)").click();
          cy.get(".btn:contains(OK)").should("not.exist");
        });
      });
    });
  });
});
