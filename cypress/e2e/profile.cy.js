describe('Profile', () => {
    it('profile', () => {
        cy.login()
        cy.visit('/profile')
        cy.get('h1').should('contain', 'test@test.de')
    })
  })