describe("Event", () => {
  [{ recurrence: false }, { recurrence: true }].forEach(function (test) {
    it("creates event with recurrence=" + test.recurrence, () => {
      cy.login();
      cy.createAdminUnit().then(function (adminUnitId) {
        cy.visit("/admin_unit/" + adminUnitId + "/events/create");

        cy.get("#name").type("Stadtfest");
        cy.checkEventStartEnd(false, test.recurrence);

        cy.select2("event_place_id", "Neu");
        cy.get("#new_event_place-location-city").type("Goslar");
        cy.get("#new_place_container_search_link").click();
        cy.select2("event_place_id", "Gos", "Goslar, 38640 Goslar");

        cy.select2("organizer_id", "Neu");
        cy.get("#new_organizer-location-city").type("Goslar");
        cy.get("#new_organizer_container_search_link").click();
        cy.select2("organizer_id", "Mei", "Meine Crew");

        cy.get("#submit").click();
        cy.url().should("include", "/actions");
        cy.get("div.alert").should(
          "contain",
          "Veranstaltung erfolgreich veröffentlicht"
        );

        cy.contains("a", "Veranstaltung bearbeiten").click();
        cy.url().should("include", "/update");
        cy.checkEventStartEnd(true, test.recurrence);
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
      cy.visit("/admin_unit/" + adminUnitId + "/events/create");

      cy.get("#name").type("Stadtfest");
      cy.select2("event_place_id", "Gos", "Goslar, 38640 Goslar");
      cy.select2("organizer_id", "Mei", "Meine Crew");

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
    cy.createAdminUnit().then(function (adminUnitId) {
      cy.createEvent(adminUnitId).then(function (eventId) {
        cy.visit("/event/" + eventId);
        cy.screenshot("read");

        cy.visit("/event/" + eventId + "/actions");
        cy.screenshot("actions");
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
        cy.visit("/event/" + eventId + "/delete");
        cy.get("#name").type("Name");
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
