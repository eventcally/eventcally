describe('Manage', () => {
    it('manage', () => {
        cy.login()
        cy.createAdminUnit().then(function(adminUnitId) {
          cy.createEvent(adminUnitId).then(function(eventId) {
            cy.visit('/manage/admin_unit/' + adminUnitId)
          })
        })
    })
  })