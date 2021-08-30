describe('Relations', () => {
    it('list', () => {
        cy.login()
        cy.createAdminUnit().then(function(adminUnitId) {
          cy.createAdminUnit("test@test.de", "Other Crew").then(function(otherAdminUnitId) {
            cy.visit('/manage/admin_unit/' + adminUnitId + "/relations")
          })
        })
    })
  })