Cypress.Commands.add('logexec', (command) => {
    cy.exec(command, { failOnNonZeroExit: false }).then(result => {
        if (result.code) {
          throw new Error(`Execution of "${command}" failed
          Exit code: ${result.code}
          Stdout:\n${result.stdout}
          Stderr:\n${result.stderr}`);
        }
      })
})

Cypress.Commands.add('setup', () => {
  cy.logexec('flask database reset --seed')
  cy.logexec('flask user create test@test.de password --confirm')
})

Cypress.Commands.add('assertValid', (fieldId) => {
  cy.get('#' + fieldId).should('have.class', 'is-valid')
  cy.get('#' + fieldId + '-error').should('be.empty')
})


Cypress.Commands.add('assertInvalid', (fieldId, msg) => {
  cy.get('#' + fieldId).should('have.class', 'is-invalid')
  cy.get('#' + fieldId + '-error').should('contain', msg)
})

Cypress.Commands.add('assertRequired', (fieldId) => {
  cy.assertInvalid(fieldId, 'Pflichtfeld')
})

Cypress.Commands.add('login', (email = "test@test.de", password = "password") => {
  cy.visit('/login')
  cy.get('#email').type(email)
  cy.get('#password').type(password)
  cy.get('#submit').click()
  cy.url().should('include', '/manage')
  cy.getCookie('session').should('exist')
})
