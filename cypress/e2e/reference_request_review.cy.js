describe("Reference request review", () => {
  it("reviews", () => {
    cy.login();
    cy.createAdminUnit().then(function (adminUnitId) {
      cy.createIncomingReferenceRequest(adminUnitId).then(function (
        referenceRequestId
      ) {
        // Reject
        cy.visit("/manage/admin_unit/" + adminUnitId + "/incoming_event_reference_request/" + referenceRequestId + "/review");
        cy.screenshot("review");
        cy.get(".decision-container .btn-danger").click();
        cy.get("#rejectFormModal select[name=rejection_reason]")
          .select("Nicht relevant")
          .should("have.value", "4");
        cy.get("#rejectFormModal").screenshot("reject");
        cy.get("#rejectFormModal .btn-danger").click();
        cy.url().should("include", "/manage/admin_unit/" + adminUnitId + "/incoming_event_reference_requests");
        cy.get("div.alert").should(
          "contain",
          "Empfehlungsanfrage erfolgreich aktualisiert"
        );
        cy.get("main .badge-pill").should("contain", "Abgelehnt");

        // Accept
        cy.visit("/manage/admin_unit/" + adminUnitId + "/incoming_event_reference_request/" + referenceRequestId + "/review");
        cy.get(".decision-container .btn-success").click();
        cy.get("#acceptFormModal select[name=rating]")
          .select("6")
          .should("have.value", "60");
        cy.get("#auto_verify").parent().click();
        cy.get("#acceptFormModal").screenshot("accept");
        cy.get("#acceptFormModal .btn-success").click();
        cy.url().should("include", "/manage/admin_unit/" + adminUnitId + "/incoming_event_reference_requests");
        cy.get("div.alert").should(
          "contain",
          "Empfehlung erfolgreich erstellt"
        );
      });
    });
  });
});
