describe("Admin unit relations", () => {
  it("list", () => {
    cy.login();
    cy.createAdminUnit().then(function (adminUnitId) {
      cy.createAdminUnit("test@test.de", "Other Crew").then(function (
        otherAdminUnitId
      ) {
        cy.visit("/manage/admin_unit/" + adminUnitId + "/outgoing_organization_relations");
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
        cy.visit("/manage/admin_unit/" + adminUnitId + "/outgoing_organization_relation/create");

        cy.select2("target_admin_unit", "Oth", "Other Crew");
        cy.screenshot("create");
        cy.get("input[type=submit]").click();

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
        cy.visit("/manage/admin_unit/" + adminUnitId + "/outgoing_organization_relation/" + relationId + "/update");
        cy.screenshot("update");
        cy.get("input[type=submit]").click();
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
        cy.visit("/manage/admin_unit/" + adminUnitId + "/outgoing_organization_relation/" + relationId + "/delete");
        cy.screenshot("update");
        cy.get("input[type=submit]").click();
        cy.url().should(
          "not.include",
          "/update"
        );
      });
    });
  });

});
