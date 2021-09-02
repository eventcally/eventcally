describe("Admin unit relations", () => {
  it("list", () => {
    cy.login();
    cy.createAdminUnit().then(function (adminUnitId) {
      cy.createAdminUnit("test@test.de", "Other Crew").then(function (
        otherAdminUnitId
      ) {
        cy.visit("/manage/admin_unit/" + adminUnitId + "/relations");
        cy.screenshot("list");
      });
    });
  });

  it("create", () => {
    cy.login();
    cy.createAdminUnit().then(function (adminUnitId) {
      cy.createAdminUnit("test@test.de", "Other Crew").then(function (
        otherAdminUnitId
      ) {
        cy.visit("/manage/admin_unit/" + adminUnitId + "/relations");
        cy.visit("/manage/admin_unit/" + adminUnitId + "/relations/create");

        cy.get("#targetOrganization input").type("ot");
        cy.get(".vbt-autcomplete-list").click();
        cy.screenshot("create");
        cy.get("button[type=submit]").click();

        cy.url().should(
          "not.include",
          "/create"
        );
      });
    });
  });

  it("updates", () => {
    cy.login();
    cy.createAdminUnit().then(function (adminUnitId) {
      cy.createAdminUnitRelation(adminUnitId).then(function (relationId) {
        cy.visit("/manage/admin_unit/" + adminUnitId + "/relations");
        cy.visit("/manage/admin_unit/" + adminUnitId + "/relations/" + relationId + "/update");
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
      cy.createAdminUnitRelation(adminUnitId).then(function (relationId) {
        cy.visit("/manage/admin_unit/" + adminUnitId + "/relations");

        cy.get('.dropdown-toggle.btn-link').click();
        cy.get('.b-dropdown.show li:last').click();

        cy.get('.dropdown-toggle.btn-link').should('not.exist');
      });
    });
  });



});
