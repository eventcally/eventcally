describe("Verification request review", () => {
  it("reviews", () => {
    cy.login();
    cy.createAdminUnit().then(function (adminUnitId) {
      cy.createIncomingVerificationRequest(adminUnitId).then(function (
        requestId
      ) {
        // Reject
        cy.visit("/manage/admin_unit/" + adminUnitId + "/incoming_organization_verification_request/" + requestId + "/review");
        cy.screenshot("review");
        cy.get(".decision-container .btn-danger").click();
        cy.get("#rejectFormModal select[name=rejection_reason]")
          .select("Nicht relevant")
          .should("have.value", "6");
        cy.get("#rejectFormModal").screenshot("reject");
        cy.get("#rejectFormModal .btn-danger").click();
        cy.url().should("include", "/incoming_organization_verification_requests");
        cy.get("div.alert").should(
          "contain",
          "Verifizierungsanfrage erfolgreich aktualisiert"
        );
        cy.get("main .badge-pill").should("contain", "Abgelehnt");

        // Accept
        cy.visit("/manage/admin_unit/" + adminUnitId + "/incoming_organization_verification_request/" + requestId + "/review");
        cy.get(".decision-container .btn-success").click();
        cy.get("#auto_verify").parent().click();
        cy.get("#acceptFormModal").screenshot("accept");
        cy.get("#acceptFormModal .btn-success").click();
        cy.url().should("include", "/incoming_organization_verification_requests");
        cy.get("div.alert").should(
          "contain",
          "Organisation erfolgreich verifiziert"
        );
      });
    });
  });
});
