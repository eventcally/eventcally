describe("Reference", () => {
  it("reads and outgoing", () => {
    cy.login();
    cy.createAdminUnit().then(function (adminUnitId) {
      cy.createIncomingReference(adminUnitId).then(function (referenceId) {
        cy.visit("/manage/admin_unit/" + adminUnitId + "/outgoing_event_references");
        cy.screenshot("outgoing");
      });
    });
  });

  it("creates", () => {
    cy.login();
    cy.createAdminUnit().then(function (adminUnitId) {
      cy.createAdminUnit("test@test.de", "Other Crew").then(function (
        otherAdminUnitId
      ) {
        cy.createEvent(otherAdminUnitId).then(function (eventId) {
          cy.visit("/event/" + eventId + "/reference");
          cy.screenshot("create");
          cy.get("#submit").click();
          cy.url().should("not.include", "/reference");
        });
      });
    });
  });

  it("updates", () => {
    cy.login();
    cy.createAdminUnit().then(function (adminUnitId) {
      cy.createIncomingReference(adminUnitId).then(function (referenceId) {
        cy.visit("/manage/admin_unit/" + adminUnitId + "/incoming_event_reference/" + referenceId + "/update");
        cy.screenshot("update");
        cy.get("#submit").click();
        cy.url().should(
          "include",
          "/manage/admin_unit/" + adminUnitId + "/incoming_event_reference/" + referenceId
        );
        cy.screenshot("incoming");
      });
    });
  });

  it("deletes", () => {
    cy.login();
    cy.createAdminUnit().then(function (adminUnitId) {
      cy.createIncomingReference(adminUnitId).then(function (referenceId) {
        cy.visit("/manage/admin_unit/" + adminUnitId + "/incoming_event_reference/" + referenceId + "/delete");
        cy.screenshot("delete");
        cy.get("#submit").click();
        cy.url().should(
          "include",
          "/manage/admin_unit/" + adminUnitId + "/incoming_event_references"
        );
      });
    });
  });
});
