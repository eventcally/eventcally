describe("OAuth2 token", () => {
  it("lists and revokes", () => {
    cy.authorize().then(function () {
      cy.visit("/user/oauth2_tokens");
      cy.screenshot("list");

      cy.get('.dropdown-toggle.btn-link').click();
      cy.get("a[href$=revoke]").click({force: true});

      cy.screenshot("revoke");
      cy.get("#submit").click();

      cy.url().should("include", "/user/oauth2_tokens");
    });
  });
});
