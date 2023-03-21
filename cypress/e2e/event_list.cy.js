describe("Event lists", () => {
  it("list", () => {
    cy.login();
    cy.createAdminUnit().then(function (adminUnitId) {
      cy.visit("/manage/admin_unit/" + adminUnitId + "/event-lists");
      cy.screenshot("list");
    });
  });

  it("create", () => {
    cy.login();
    cy.createAdminUnit().then(function (adminUnitId) {
        cy.visit("/manage/admin_unit/" + adminUnitId + "/event-lists");
        cy.visit("/manage/admin_unit/" + adminUnitId + "/event-lists/create");

        cy.get('input[name=name]').type("Sehr gute Liste");
        cy.screenshot("create");
        cy.get("button[type=submit]").click();

        cy.url().should(
          "not.include",
          "/create"
        );

        cy.get('button:contains(Sehr)');
        cy.screenshot("list-filled");
    });
  });

  it("read", () => {
    cy.login();
    cy.createAdminUnit().then(function (adminUnitId) {
      cy.createEventList(adminUnitId).then(function (eventListId) {
        cy.visit("/manage/admin_unit/" + adminUnitId + "/event-lists/" + eventListId);
        cy.screenshot("read");
      });
    });
  });

  it("updates", () => {
    cy.login();
    cy.createAdminUnit().then(function (adminUnitId) {
      cy.createEventList(adminUnitId).then(function (eventListId) {
        cy.visit("/manage/admin_unit/" + adminUnitId + "/event-lists");
        cy.visit("/manage/admin_unit/" + adminUnitId + "/event-lists/" + eventListId + "/update");
        cy.screenshot("update");
        cy.get("button[type=submit]").click();
        cy.url().should(
          "not.include",
          "/update"
        );
      });
    });
  });

  it("deletes", () => {
    cy.login();
    cy.createAdminUnit().then(function (adminUnitId) {
      cy.createEventList(adminUnitId).then(function (eventListId) {
        cy.visit("/manage/admin_unit/" + adminUnitId + "/event-lists");

        cy.get('.dropdown-toggle.btn-link').click();
        cy.get('.b-dropdown.show li:last').click();

        cy.get('.dropdown-toggle.btn-link').should('not.exist');
      });
    });
  });
});
