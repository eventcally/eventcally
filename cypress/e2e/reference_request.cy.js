describe("Reference request", () => {
  it("lists", () => {
    cy.login();
    cy.createAdminUnit().then(function (adminUnitId) {
      cy.createIncomingReferenceRequest(adminUnitId).then(function (
        referenceRequestId
      ) {
        cy.visit(
          "/manage/admin_unit/" + adminUnitId + "/incoming_event_reference_requests"
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
          cy.visit("/manage/admin_unit/" + adminUnitId + "/outgoing_event_reference_request/create_for_event/" + eventId);
          cy.select2("admin_unit", "Oth", "Other Crew");
          cy.screenshot("create");
          cy.get("#submit").click();
          cy.url().should("include", "/manage/admin_unit/" + adminUnitId + "/outgoing_event_reference_requests");
          cy.screenshot("outgoing");
        });
      });
    });
  });
});
