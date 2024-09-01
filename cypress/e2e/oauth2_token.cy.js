describe("OAuth2 token", () => {
  it("lists and revokes", () => {
    cy.authorize().then(function () {
      cy.visit("/user/oauth2_tokens");
      cy.screenshot("list");

      cy.get("a[href$=revoke]").click();
      cy.screenshot("revoke");
      cy.get("#submit").click();

      cy.url().should("include", "/user/oauth2_tokens");
    });
  });
});
