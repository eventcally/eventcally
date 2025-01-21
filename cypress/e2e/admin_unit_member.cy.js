describe("Admin Unit Member", () => {
  it("updates", () => {
    cy.login();
    cy.createAdminUnit().then(function (adminUnitId) {
      cy.createUser("new@test.de").then(function () {
        cy.createAdminUnitMember(adminUnitId, "new@test.de").then(function (
          memberId
        ) {
          cy.visit("/manage/admin_unit/" + adminUnitId + "/organization_member/" + memberId + "/update");
          cy.screenshot("update");
          cy.get("#submit").click();
          cy.url().should(
            "include",
            "/manage/admin_unit/" + adminUnitId + "/organization_members"
          );
          cy.screenshot("list");
        });
      });
    });
  });

  it("deletes", () => {
    cy.login();
    cy.createAdminUnit().then(function (adminUnitId) {
      cy.createUser("new@test.de").then(function () {
        cy.createAdminUnitMember(adminUnitId, "new@test.de").then(function (
          memberId
        ) {
          cy.visit("/manage/admin_unit/" + adminUnitId + "/organization_member/" + memberId + "/delete");
          cy.screenshot("delete");
          cy.get("#submit").click();
          cy.url().should(
            "include",
            "/manage/admin_unit/" + adminUnitId + "/organization_members"
          );
        });
      });
    });
  });
});
