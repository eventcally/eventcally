describe("Admin Unit Member Invitation", () => {
  it("creates", () => {
    cy.login();
    cy.createAdminUnit().then(function (adminUnitId) {
      cy.visit("/manage/admin_unit/" + adminUnitId + "/organization_member_invitation/create");
      cy.get("#email").type("new@test.de");
      cy.screenshot("create");
      cy.get("#submit").click();
      cy.url().should(
        "include",
        "/manage/admin_unit/" + adminUnitId + "/organization_member_invitations"
      );
    });
  });

  it("deletes", () => {
    cy.login();
    cy.createAdminUnit().then(function (adminUnitId) {
      cy.createAdminUnitMemberInvitation(adminUnitId).then(function (
        invitationId
      ) {
        cy.visit("/manage/admin_unit/" + adminUnitId + "/organization_member_invitation/" + invitationId + "/delete");
        cy.screenshot("delete");
        cy.get("#submit").click();
        cy.url().should(
          "include",
          "/manage/admin_unit/" + adminUnitId + "/organization_member_invitations"
        );
      });
    });
  });

  it("reads", () => {
    cy.login();
    cy.createAdminUnit().then(function (adminUnitId) {
      cy.createAdminUnitMemberInvitation(adminUnitId, "test@test.de").then(
        function (invitationId) {
          cy.visit("/invitations/" + invitationId);
          cy.get("#accept").click();
          cy.url().should(
            "include",
            "/manage/admin_unit/" + adminUnitId + "/events"
          );
        }
      );
    });
  });
});
