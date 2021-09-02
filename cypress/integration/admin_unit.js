describe("Admin Unit", () => {
  it("creates", () => {
    cy.login();
    cy.visit("/admin_unit/create");
    cy.get("#name").type("Second Crew");
    cy.get("#location-postalCode").type("38640");
    cy.get("#location-city").type("Goslar");
    cy.screenshot("create");
    cy.get("#submit").click();
    cy.url().should("include", "/manage/admin_unit/");
  });

  it("updates", () => {
    cy.login();
    cy.createAdminUnit().then(function (adminUnitId) {
      cy.visit("/admin_unit/" + adminUnitId + "/update");
      cy.screenshot("update");
      cy.get("#submit").click();
      cy.url().should("include", "/admin_unit/" + adminUnitId + "/update");
      cy.get("div.alert").should(
        "contain",
        "Organisation erfolgreich aktualisiert"
      );
    });
  });

  it("widgets", () => {
    cy.login();
    cy.createAdminUnit().then(function (adminUnitId) {
      cy.visit("/manage/admin_unit/" + adminUnitId + "/widgets");
      cy.get("#toggle-settings-btn").click();
      cy.screenshot("widgets");
      cy.get("#submit").click();
      cy.url().should(
        "include",
        "/manage/admin_unit/" + adminUnitId + "/widgets"
      );
      cy.get("div.alert").should(
        "contain",
        "Einstellungen erfolgreich aktualisiert"
      );
    });
  });
});
