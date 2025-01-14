describe("Verification request", () => {
  it("lists", () => {
    cy.login();
    cy.createAdminUnit().then(function (adminUnitId) {
      cy.createIncomingVerificationRequest(adminUnitId).then(function (
        requestId
      ) {
        cy.visit(
          "/manage/admin_unit/" + adminUnitId + "/incoming_admin_unit_verification_requests"
        );
        cy.screenshot("incoming");
      });
    });
  });

  it("creates", () => {
    cy.login();
    cy.createAdminUnit().then(function (adminUnitId) {
      cy.createAdminUnit("test@test.de", "Other Crew", false).then(function (otherAdminUnitId) {
        cy.visit("/manage/admin_unit/" + otherAdminUnitId + "/verification_requests/outgoing/create/select");
        cy.screenshot("create-select");
        cy.get(".btn-primary:first").click();

        cy.url().should("include", "/verification_requests/outgoing/create/target");
        cy.screenshot("create");
        cy.get("#submit").click();

        cy.url().should("include", "/outgoing_admin_unit_verification_requests");
        cy.screenshot("outgoing");

        // Status
        cy.get('.dropdown-toggle.btn-link').click();
        cy.get('a:contains(Anzeigen)').click({force: true});
        cy.url().should("include", "/outgoing_admin_unit_verification_request/");
        cy.screenshot("status");
      });
    });
  });
});
