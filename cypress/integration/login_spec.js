describe('Login', () => {
    it('user log in', () => {
        cy.visit('/login')

        // Blank
        cy.get('#submit').click()
        cy.assertRequired('email')
        cy.assertRequired('password')

        // Email
        cy.get('#email').type("invalidmail")
        cy.assertInvalid('email', 'Geben Sie bitte eine gültige E-Mail-Adresse ein.')

        cy.get('#email').clear().type("test@test.de")
        cy.assertValid('email')

        // Password
        cy.get('#password').type("password")
        cy.assertValid('password')

        // Submit
        cy.get('#submit').click()

        cy.url().should('include', '/manage')
        cy.get('h1').should('contain', 'Organisationen')
        cy.getCookie('session').should('exist')
    })
  })