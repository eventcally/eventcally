describe("Admin Unit Member Invitation", () => {
  it("creates", () => {
    cy.login();
    cy.createAdminUnit().then(function (adminUnitId) {
      cy.visit("/manage/admin_unit/" + adminUnitId + "/members/invite");
      cy.get("#email").type("new@test.de");
      cy.screenshot("create");
      cy.get("#submit").click();
      cy.url().should(
        "include",
        "/manage/admin_unit/" + adminUnitId + "/members"
      );
    });
  });

  it("deletes", () => {
    cy.login();
    cy.createAdminUnit().then(function (adminUnitId) {
      cy.createAdminUnitMemberInvitation(adminUnitId).then(function (
        invitationId
      ) {
        cy.visit("/manage/invitation/" + invitationId + "/delete");
        cy.get("#email").type("new@test.de");
        cy.screenshot("delete");
        cy.get("#submit").click();
        cy.url().should(
          "include",
          "/manage/admin_unit/" + adminUnitId + "/members"
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
