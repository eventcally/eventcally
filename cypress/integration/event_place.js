describe("Event place", () => {
  it("creates", () => {
    cy.login();
    cy.createAdminUnit().then(function (adminUnitId) {
      cy.visit("/manage/admin_unit/" + adminUnitId + "/places/create");
      cy.get("#name").type("Mein Platz");
      cy.screenshot("create");
      cy.get("#submit").click();
      cy.url().should(
        "include",
        "/manage/admin_unit/" + adminUnitId + "/event_places"
      );
      cy.screenshot("list");
    });
  });

  it("updates", () => {
    cy.login();
    cy.createAdminUnit().then(function (adminUnitId) {
      cy.createEventPlace(adminUnitId).then(function (eventPlaceId) {
        cy.visit("/event_place/" + eventPlaceId + "/update");
        cy.screenshot("update");
        cy.get("#submit").click();
        cy.url().should(
          "include",
          "/manage/admin_unit/" + adminUnitId + "/event_places"
        );
      });
    });
  });

  it("deletes", () => {
    cy.login();
    cy.createAdminUnit().then(function (adminUnitId) {
      cy.createEventPlace(adminUnitId).then(function (eventPlaceId) {
        cy.visit("/event_place/" + eventPlaceId + "/delete");
        cy.get("#name").type("Mein Platz");
        cy.screenshot("delete");
        cy.get("#submit").click();
        cy.url().should(
          "include",
          "/manage/admin_unit/" + adminUnitId + "/event_places"
        );
      });
    });
  });
});
