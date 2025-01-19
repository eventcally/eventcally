describe("Admin unit organization invitations", () => {
  it("list", () => {
    cy.login();
    cy.createAdminUnit().then(function (adminUnitId) {
      cy.visit("/manage/admin_unit/" + adminUnitId + "/organization_invitations");
      cy.screenshot("list");
    });
  });

  it("create", () => {
    cy.login();
    cy.createAdminUnit().then(function (adminUnitId) {
        cy.visit("/manage/admin_unit/" + adminUnitId + "/organization_invitations");
        cy.visit("/manage/admin_unit/" + adminUnitId + "/organization_invitation/create");

        cy.get('input[name=email]').type("invited@test.de");
        cy.get('input[name=admin_unit_name]').type("Invited organization");
        cy.screenshot("create");
        cy.get("input[type=submit]").click();

        cy.url().should(
          "not.include",
          "/create"
        );

        cy.get('button:contains(invited@test.de)');
        cy.screenshot("list-filled");
    });
  });

  it("updates", () => {
    cy.login();
    cy.createAdminUnit().then(function (adminUnitId) {
      cy.createAdminUnitOrganizationInvitation(adminUnitId).then(function (invitationId) {
        cy.visit("/manage/admin_unit/" + adminUnitId + "/organization_invitations");
        cy.visit("/manage/admin_unit/" + adminUnitId + "/organization_invitation/" + invitationId + "/update");
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
      cy.createAdminUnitOrganizationInvitation(adminUnitId).then(function (invitationId) {
        cy.visit("/manage/admin_unit/" + adminUnitId + "/organization_invitations");
        cy.visit("/manage/admin_unit/" + adminUnitId + "/organization_invitation/" + invitationId + "/delete");
        cy.screenshot("delete");
        cy.get("input[type=submit]").click();
        cy.url().should(
          "not.include",
          "/delete"
        );
      });
    });
  });
});
