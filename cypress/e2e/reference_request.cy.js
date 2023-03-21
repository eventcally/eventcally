describe("Reference request", () => {
  it("lists", () => {
    cy.login();
    cy.createAdminUnit().then(function (adminUnitId) {
      cy.createIncomingReferenceRequest(adminUnitId).then(function (
        referenceRequestId
      ) {
        cy.visit(
          "/manage/admin_unit/" + adminUnitId + "/reference_requests/incoming"
        );
        cy.screenshot("incoming");
      });
    });
  });

  it("creates", () => {
    cy.login();
    cy.createAdminUnit().then(function (adminUnitId) {
      cy.createAdminUnit("test@test.de", "Other Crew").then(function (otherAdminUnitId) {
        cy.createEvent(adminUnitId).then(function (eventId) {
          cy.visit("/event/" + eventId + "/reference_request/create");
          cy.screenshot("create");
          cy.get("#submit").click();
          cy.url().should("include", "/reference_requests/outgoing");
          cy.screenshot("outgoing");
        });
      });
    });
  });
});
