describe("Event", () => {
  [{ recurrence: false }, { recurrence: true }].forEach(function (test) {
    it("creates event with recurrence=" + test.recurrence, () => {
      cy.login();
      cy.createAdminUnit().then(function (adminUnitId) {
        cy.visit("/manage/admin_unit/" + adminUnitId + "/event/create");

        cy.get("#name").type("Stadtfest");
        cy.checkEventStartEnd(false, test.recurrence, "date_definitions-0-");

        cy.get("#add-date-defintion-btn").click();
        cy.checkEventStartEnd(false, test.recurrence, "date_definitions-1-");

        cy.get('#event_place_choice-1').click();
        cy.get("#new_event_place-location-city").type("Goslar");
        cy.get('#event_place_choice-0').click();
        cy.select2("event_place", "Gos", "Goslar, 38640 Goslar");

        cy.get('#organizer_choice-1').click();
        cy.get("#new_organizer-location-city").type("Goslar");
        cy.get('#organizer_choice-0').click();
        cy.select2("organizer", "Mei", "Meine Crew");

        cy.get("#submit").click();
        cy.url().should("include", "/actions");
        cy.get("div.alert").should(
          "contain",
          "Veranstaltung erfolgreich veröffentlicht"
        );

        cy.contains("a", "Veranstaltung bearbeiten").click();
        cy.url().should("include", "/update");

        cy.checkEventStartEnd(true, test.recurrence, "date_definitions-0-");

        cy.get('div[data-prefix=date_definitions-1-] .remove-date-defintion-btn:visible').click()

        cy.get("#submit").click();
        cy.url().should(
          "include",
          "/manage/admin_unit/" + adminUnitId + "/events"
        );
        cy.get("div.alert").should(
          "contain",
          "Veranstaltung erfolgreich aktualisiert"
        );
      });
    });
  });

  it("saves draft", () => {
    cy.login();
    cy.createAdminUnit().then(function (adminUnitId) {
      cy.visit("/manage/admin_unit/" + adminUnitId + "/event/create");

      cy.get("#name").type("Stadtfest");
      cy.select2("event_place", "Gos", "Goslar, 38640 Goslar");
      cy.select2("organizer", "Mei", "Meine Crew");

      cy.get("#submit_draft").click();
      cy.url().should("include", "/actions");
      cy.get("div.alert").should(
        "contain",
        "Entwurf erfolgreich gespeichert"
      );

      cy.contains("a", "Veranstaltung bearbeiten").click();
      cy.url().should("include", "/update");
      cy.get("#public_status").should('have.value', '1')
      cy.get("#submit").click();
      cy.url().should(
        "include",
        "/manage/admin_unit/" + adminUnitId + "/events"
      );
      cy.get("div.alert").should(
        "contain",
        "Veranstaltung erfolgreich aktualisiert"
      );
      cy.screenshot("list");

      cy.visit("/manage/admin_unit/" + adminUnitId + "/events");
      cy.get('main .badge-pill').should('contain', 'Entwurf')
    });
  });

  it("read and actions", () => {
    cy.login();
    cy.createAdminUnit().then(function (adminUnitId) {
      cy.createEvent(adminUnitId).then(function (eventId) {
        cy.createEventList(adminUnitId).then(function (eventListId) {
          cy.visit("/event/" + eventId);
          cy.screenshot("read");

          cy.visit("/event/" + eventId + "/actions");
          cy.screenshot("actions");

          cy.wait(1000); // Wait for Vue to load
          cy.get("a:contains(Zu Liste)").click();
          cy.get(".btn:contains(OK)").should("be.visible");
          cy.screenshot("lists");

          cy.get(".btn:contains(OK)").click();
          cy.get(".btn:contains(OK)").should("not.exist");
        });
      });
    });
  });

  it("report", () => {
    cy.createAdminUnit().then(function (adminUnitId) {
      cy.createEvent(adminUnitId).then(function (eventId) {
        cy.visit("/event/" + eventId + "/report");

        cy.get("input[name=contactName]").type("Firstname Lastname");
        cy.get("input[name=contactEmail]").type("firstname.lastname@test.de");
        cy.get("textarea[name=message]").type("Die Veranstaltung kann leider nicht stattfinden.");
        cy.screenshot("report");
        cy.get("button[type=submit]").click();

        cy.get('button[type=submit]').should('not.exist');
        cy.screenshot("report-submitted");
      });
    });
  });

  it("deletes", () => {
    cy.login();
    cy.createAdminUnit().then(function (adminUnitId) {
      cy.createEvent(adminUnitId).then(function (eventId) {
        cy.visit("/manage/admin_unit/" + adminUnitId + "/event/" + eventId + "/delete");
        cy.screenshot("delete");
        cy.get("#submit").click();
        cy.url().should(
          "include",
          "/manage/admin_unit/" + adminUnitId + "/events"
        );
      });
    });
  });

});
