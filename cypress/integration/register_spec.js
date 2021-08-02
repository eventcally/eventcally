describe('Register', () => {
    beforeEach(() => {
        cy.exec('flask database reset --seed')
    })


    it('registers user', () => {
        cy.visit('/register')
        cy.get('input[name=email]').type("firstname.lastname@gmail.com")
        cy.get('input[name=password]').type("iloveoveda{enter}")
        cy.get('input[name=password_confirm]').type("iloveoveda{enter}")
        cy.get('input[name=accept_tos]').check()
        cy.get('input[name=submit]').click()

        cy.url().should('eq', Cypress.config().baseUrl + '/')
        cy.get('div.alert').should('contain', 'Bestätigungsanleitung')
    })
  })