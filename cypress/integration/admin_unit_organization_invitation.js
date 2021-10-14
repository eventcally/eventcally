describe("Admin unit organization invitations", () => {
  it("list", () => {
    cy.login();
    cy.createAdminUnit().then(function (adminUnitId) {
      cy.visit("/manage/admin_unit/" + adminUnitId + "/organization-invitations");
      cy.screenshot("list");
    });
  });

  it("create", () => {
    cy.login();
    cy.createAdminUnit().then(function (adminUnitId) {
        cy.visit("/manage/admin_unit/" + adminUnitId + "/organization-invitations");
        cy.visit("/manage/admin_unit/" + adminUnitId + "/organization-invitations/create");

        cy.get('input[name=email]').type("invited@test.de");
        cy.get('input[name=organizationName]').type("Invited organization");
        cy.screenshot("create");
        cy.get("button[type=submit]").click();

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
        cy.visit("/manage/admin_unit/" + adminUnitId + "/organization-invitations");
        cy.visit("/manage/admin_unit/" + adminUnitId + "/organization-invitations/" + invitationId + "/update");
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
      cy.createAdminUnitOrganizationInvitation(adminUnitId).then(function (invitationId) {
        cy.visit("/manage/admin_unit/" + adminUnitId + "/organization-invitations");

        cy.get('.dropdown-toggle.btn-link').click();
        cy.get('.b-dropdown.show li:last').click();

        cy.get('.dropdown-toggle.btn-link').should('not.exist');
      });
    });
  });
});
