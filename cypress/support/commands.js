Cypress.Commands.add('logexec', (command) => {
    return cy.exec(command, { failOnNonZeroExit: false }).then(function(result) {
        if (result.code) {
          throw new Error(`Execution of "${command}" failed
          Exit code: ${result.code}
          Stdout:\n${result.stdout}
          Stderr:\n${result.stderr}`)
        }

        return result;
      })
})

Cypress.Commands.add('setup', () => {
  cy.logexec('flask test reset --seed')
  cy.logexec('flask user create test@test.de password --confirm')
})

Cypress.Commands.add('createAdminUnit', (userEmail = 'test@test.de', name = 'Meine Crew') => {
  return cy.logexec('flask test admin-unit-create ' + userEmail + ' "' + name + '"').then(function(result) {
    let json = JSON.parse(result.stdout)
    return json.admin_unit_id
  })
})

Cypress.Commands.add('createEvent', (adminUnitId) => {
  return cy.logexec('flask test event-create ' + adminUnitId).then(function(result) {
    let json = JSON.parse(result.stdout)
    return json.event_id
  })
})

Cypress.Commands.add('createIncomingReferenceRequest', (adminUnitId) => {
  return cy.logexec('flask test reference-request-create-incoming ' + adminUnitId).then(function(result) {
    let json = JSON.parse(result.stdout)
    return json.reference_request_id
  })
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

Cypress.Commands.add('select2', (selectId, textToEnter, expectedText = null, expectedValue = null) => {
  cy.get('#select2-' + selectId + '-container').click()
  cy.get('input[aria-controls="select2-' + selectId + '-results"]')
    .type(textToEnter + '{enter}', {
        delay: 500,
    })

  if (expectedText) {
    cy.get('#select2-' + selectId + '-container').should('have.text', expectedText)
  }

  if (expectedValue) {
    cy.get('#' + selectId).should('have.value', expectedValue)
  }
})