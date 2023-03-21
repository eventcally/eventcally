describe("Suggestion", () => {
  it("reject", () => {
    cy.login();
    cy.createAdminUnit().then(function (adminUnitId) {
      cy.createSuggestion(adminUnitId).then(function (suggestionId) {
        cy.visit("/event_suggestion/" + suggestionId + "/review_status");
        cy.screenshot("status");

        cy.visit("/event_suggestion/" + suggestionId + "/review");
        cy.screenshot("review");

        cy.get(".decision-container .btn-danger").click();
        cy.get("#rejectFormModal select[name=rejection_resaon]")
          .select("Duplikat")
          .should("have.value", "1");
        cy.get("#rejectFormModal").screenshot("reject");
        cy.get("#rejectFormModal .btn-danger").click();

        cy.url().should("include", "/reviews");
        cy.get("div.alert").should(
          "contain",
          "Veranstaltungsvorschlag erfolgreich abgelehnt"
        );
        cy.get("main .badge-pill").should("contain", "Abgelehnt");
        cy.screenshot("list");
      });
    });
  });
});
