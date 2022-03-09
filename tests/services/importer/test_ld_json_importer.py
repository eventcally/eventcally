from tests.sub_tests import SubTests


class TestLdJsonImporter(SubTests):
    def test_load_event_from_ld_json(self, client, seeder, utils, app, shared_datadir):
        self.utils = utils
        self.shared_datadir = shared_datadir

        with app.app_context():
            self.call_sub_tests()

    def _test_category(self):
        def manipulate(ld_json):
            ld_json["@type"] = "MusicEvent"

        event = self._load_event_from_ld_json(manipulate)
        assert event.categories[0].name == "Music"

    def _test_booked_up_ausgebucht(self):
        def manipulate(ld_json):
            ld_json["eventStatus"] = "ausgebucht"

        event = self._load_event_from_ld_json(manipulate)
        assert event.booked_up

    def _test_default(self):
        event = self._load_event_from_ld_json()
        assert event is not None

    def _test_accessible_for_free(self):
        def manipulate(ld_json):
            ld_json["isAccessibleForFree"] = True

        event = self._load_event_from_ld_json(manipulate)
        assert event.accessible_for_free

    def _test_no_organizer_but_author(self):
        def manipulate(ld_json):
            ld_json["author"] = ld_json["organizer"]
            del ld_json["organizer"]

        event = self._load_event_from_ld_json(manipulate)
        assert event is not None

    def _test_null_organizer_but_author(self):
        def manipulate(ld_json):
            ld_json["author"] = ld_json["organizer"]
            ld_json["organizer"] = [None]

        event = self._load_event_from_ld_json(manipulate)
        assert event is not None

    def _test_no_organizer(self):
        import pytest

        def manipulate(ld_json):
            del ld_json["organizer"]

        with pytest.raises(Exception):
            self._load_event_from_ld_json(manipulate)

    def _test_photo_empty_list(self):
        def manipulate(ld_json):
            ld_json["image"] = []

        event = self._load_event_from_ld_json(manipulate)
        assert event is not None

    def _test_photo_no_url(self):
        def manipulate(ld_json):
            ld_json["image"] = {}

        event = self._load_event_from_ld_json(manipulate)
        assert event is not None

    def _test_photo_contributor(self):
        self.utils.mock_image_request_with_file(
            "https://example.org/image",
            self.shared_datadir,
            "image500.png",
        )

        def manipulate(ld_json):
            ld_json["image"] = {
                "url": "https://example.org/image",
                "contributor": "Contributor",
            }

        event = self._load_event_from_ld_json(manipulate)
        assert event.photo.copyright_text == "Contributor"

    def _load_event_from_ld_json(self, manipulate_json=None):
        from project.services.importer.ld_json_importer import LdJsonImporter

        ld_json = self._create_ld_json()

        if manipulate_json:
            manipulate_json(ld_json)

        importer = LdJsonImporter("", "")
        importer.ld_json = importer._strip_ld_json(ld_json)
        event = importer.load_event_from_ld_json()

        return event

    def _create_ld_json(self):
        return {
            "@type": "Event",
            "location": [
                {
                    "@type": "Place",
                    "address": {
                        "@type": "PostalAddress",
                        "addressCountry": "Deutschland",
                        "addressLocality": "Wernigerode OT Schierke",
                        "postalCode": "38879",
                        "streetAddress": "Am Winterbergtor 2",
                    },
                    "name": "Schierker Feuerstein Arena",
                }
            ],
            "name": "Name",
            "organizer": [
                {
                    "@type": ["Organization"],
                    "address": {
                        "@type": "PostalAddress",
                        "addressLocality": "Wernigerode OT Schierke",
                        "postalCode": "38879",
                        "streetAddress": "Am Winterbergtor 2",
                    },
                    "email": "sfa@wernigerode.de",
                    "name": " Schierker Feuerstein Arena",
                    "telephone": "03943 - 654 777",
                    "faxNumber": "03943 - 654 778",
                    "url": "http://www.schierker-feuerstein-arena.de",
                }
            ],
            "startDate": "2021-07-10T11:00:00+02:00",
            "url": "https://www.harzinfo.de/veranstaltungen/event/3-schierker-biathlon-challenge-mit-michael-roesch",
        }
