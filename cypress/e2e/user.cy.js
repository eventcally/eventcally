describe("User", () => {
   it("registers user", () => {
    cy.visit("/register");
    cy.screenshot("register");

    // Blank
    cy.get("#submit").click();
    cy.assertRequired("email");
    cy.assertRequired("password");
    cy.assertRequired("password_confirm");
    cy.assertRequired("accept_tos");

    // Email
    cy.get("#email").type("invalidmail");
    cy.assertInvalid(
      "email",
      "Geben Sie bitte eine gültige E-Mail-Adresse ein."
    );

    cy.get("#email").clear().type("test@test.de");
    cy.assertInvalid(
      "email",
      "Mit dieser E-Mail existiert bereits ein Account."
    );

    cy.get("#email").clear().type("firstname.lastname@gmail.com");
    cy.assertValid("email");

    // Password
    cy.get("#password").type("short");
    cy.assertInvalid("password", "Geben Sie bitte mindestens 8 Zeichen ein.");

    cy.get("#password").clear().type("iloveeventcally");
    cy.assertValid("password");

    // Confirm password
    cy.get("#password_confirm").type("different");
    cy.assertInvalid(
      "password_confirm",
      "Wiederholen Sie bitte denselben Wert."
    );

    cy.get("#password_confirm").clear().type("iloveeventcally");
    cy.assertValid("password_confirm");

    // Submit
    cy.get("#accept_tos").check();
    cy.get("#submit").click();

    cy.url().should("eq", Cypress.config().baseUrl + "/");
    cy.get("div.alert").should("contain", "bestätigen");
  });

   it("login", () => {
    cy.visit("/login");
    cy.screenshot("login");

    // Blank
    cy.get("#submit").click();
    cy.assertRequired("email");
    cy.assertRequired("password");

    // Email
    cy.get("#email").type("invalidmail");
    cy.assertInvalid(
      "email",
      "Geben Sie bitte eine gültige E-Mail-Adresse ein."
    );

    cy.get("#email").clear().type("test@test.de");
    cy.assertValid("email");

    // Password
    cy.get("#password").type("password");
    cy.assertValid("password");

    // Submit
    cy.get("#submit").click();

    cy.url().should("include", "/manage");
    cy.get("h1").should("contain", "Organisationen");
    cy.getCookie("session").should("exist");

    // Profile
    cy.visit("/profile");
    cy.screenshot("profile");
  });
});
