describe("Event organizer", () => {
  it("creates", () => {
    cy.login();
    cy.createAdminUnit().then(function (adminUnitId) {
      cy.visit("/manage/admin_unit/" + adminUnitId + "/event_organizer/create");
      cy.get("#name").type("Mein Veranstalter");
      cy.screenshot("create");
      cy.get("#submit").click();
      cy.url().should(
        "include",
        "/manage/admin_unit/" + adminUnitId + "/event_organizers"
      );
      cy.screenshot("list");
    });
  });

  it("updates", () => {
    cy.login();
    cy.createAdminUnit().then(function (adminUnitId) {
      cy.createEventOrganizer(adminUnitId).then(function (eventOrganizerId) {
        cy.visit("/manage/admin_unit/" + adminUnitId + "/event_organizer/" + eventOrganizerId + "/update");
        cy.screenshot("update");
        cy.get("#submit").click();
        cy.url().should(
          "include",
          "/manage/admin_unit/" + adminUnitId + "/event_organizers"
        );
      });
    });
  });

  it("deletes", () => {
    cy.login();
    cy.createAdminUnit().then(function (adminUnitId) {
      cy.createEventOrganizer(adminUnitId).then(function (eventOrganizerId) {
        cy.visit("/manage/admin_unit/" + adminUnitId + "/event_organizer/" + eventOrganizerId + "/delete");
        cy.get("#name").type("Mein Veranstalter");
        cy.screenshot("delete");
        cy.get("#submit").click();
        cy.url().should(
          "include",
          "/manage/admin_unit/" + adminUnitId + "/event_organizers"
        );
      });
    });
  });
});
