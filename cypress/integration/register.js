describe('Register', () => {
    it('registers user', () => {
        cy.visit('/register')

        // Blank
        cy.get('#submit').click()
        cy.assertRequired('email')
        cy.assertRequired('password')
        cy.assertRequired('password_confirm')
        cy.assertRequired('accept_tos')

        // Email
        cy.get('#email').type("invalidmail")
        cy.assertInvalid('email', 'Geben Sie bitte eine gültige E-Mail-Adresse ein.')

        cy.get('#email').clear().type("test@test.de")
        cy.assertInvalid('email', 'Mit dieser E-Mail existiert bereits ein Account.')

        cy.get('#email').clear().type("firstname.lastname@gmail.com")
        cy.assertValid('email')

        // Password
        cy.get('#password').type("short")
        cy.assertInvalid('password', 'Geben Sie bitte mindestens 8 Zeichen ein.')

        cy.get('#password').clear().type("iloveoveda")
        cy.assertValid('password')

        // Confirm password
        cy.get('#password_confirm').type("different")
        cy.assertInvalid('password_confirm', 'Wiederholen Sie bitte denselben Wert.')

        cy.get('#password_confirm').clear().type("iloveoveda")
        cy.assertValid('password_confirm')

        // Submit
        cy.get('#accept_tos').check()
        cy.get('#submit').click()

        cy.url().should('eq', Cypress.config().baseUrl + '/')
        cy.get('div.alert').should('contain', 'Bestätigungsanleitung')
    })
  })