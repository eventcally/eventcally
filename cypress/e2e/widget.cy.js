describe("Widget", () => {
  it("event dates", () => {
    cy.createAdminUnit().then(function (adminUnitId) {
      cy.createEvent(adminUnitId).then(function (eventId) {
        cy.visit("/organization/" + adminUnitId + "/widget/eventdates");
        cy.screenshotDatepicker("#date_from-user");
        cy.screenshot("eventdates");

        cy.get(".stretched-link")
          .invoke("attr", "href")
          .then((href) => {
            cy.visit(href);
            cy.screenshot("event-date");
          });
      });
    });
  });

  [
    {
      recurrence: false,
      suffix: true,
    },
    {
      recurrence: true,
      suffix: false,
    },
  ].forEach(function (test) {
    it(
      "creates suggestion with recurrence=" +
        test.recurrence +
        ", suffix=" +
        test.suffix,
      () => {
        cy.createAdminUnit().then(function (adminUnitId) {
          // Start
          cy.visit("/organization/" + adminUnitId + "/widget/event_suggestions/create");
          cy.wait(1000); // Wait for jQuery to load
          cy.get(".wizard-next:visible").click();

          // Tos
          cy.get("#accept_tos").check();
          cy.get(".wizard-next:visible").click();

          // Contact
          cy.get("#contact_name").type("Vorname Nachname");
          cy.get("#contact_email").type("vorname.nachname@domain.de");
          cy.get(".wizard-next:visible").click();

          // Required fields
          cy.get("#name").type("Vorschlag");

          cy.get("#event_place_id_suffix").should("not.exist");
          cy.select2("event_place_id", "Neu", "Neu");
          cy.get("#event_place_id_suffix").type("Adresse");

          if (!test.suffix) {
            cy.select2("event_place_id", "Gos", "Goslar");
            cy.get("#event_place_id_suffix").should("not.exist");
          }

          cy.get("#organizer_id_suffix").should("not.exist");
          cy.select2("organizer_id", "Neu", "Neu");
          cy.get("#organizer_id_suffix").type("Adresse");

          if (!test.suffix) {
            cy.select2("organizer_id", "Cre", "Meine Crew");
            cy.get("#organizer_id_suffix").should("not.exist");
          }

          cy.checkEventStartEnd(false, test.recurrence);
          cy.get(".wizard-next:visible").click();

          // Photo
          cy.get("#photo-copyright_text").type("2021");
          cy.get(".wizard-next:visible").click();

          // Optional details
          cy.get("#description").type("Beschreibung");
          cy.get(".wizard-next:visible").click();

          cy.get("#submit").click();
          cy.url().should("include", "/review_status");
          cy.get("div.alert").should(
            "contain",
            "Die Veranstaltung wird geprüft."
          );
        });
      }
    );
  });
});
