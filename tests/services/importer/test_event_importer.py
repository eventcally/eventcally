import pytest


# Load more urls:
# curl -o tests/services/importer/data/<filename>.html <URL>
def test_import(client, seeder, utils, app, shared_datadir, requests_mock):
    _, admin_unit_id = seeder.setup_base()
    seeder.upsert_event_place(admin_unit_id, "MINER'S ROCK")
    seeder.upsert_event_organizer(admin_unit_id, "MINER'S ROCK")

    params = (utils, admin_unit_id, shared_datadir)

    with app.app_context():
        _assert_import_event(
            params,
            "facebook.html",
            "https://www.facebook.com/events/413124792931487",
            "https://m.facebook.com/events/413124792931487",
        )

        _assert_import_event(
            params,
            "regiondo.html",
            "https://goslar.regiondo.de/unterwegs-mit-der-frau-des-nachtwachters",
        )

        _assert_import_event(
            params,
            "eventim.html",
            "https://www.eventim.de/event/kaisermania-2022-roland-kaiser-live-mit-band-filmnaechte-am-elbufer-14339901/",
        )

        _assert_import_event(
            params,
            "meetup.html",
            "https://www.meetup.com/de-DE/hi-new-work/events/282743665/",
        )

        _assert_import_event(
            params,
            "reservix.html",
            "https://kultur-kraftwerk.reservix.de/tickets-christoph-kuch-ich-weiss-in-goslar-kulturkraftwerk-harzenergie-am-14-1-2022/e1739715",
            "https://www.reservix.de/tickets-christoph-kuch-ich-weiss-in-goslar-kulturkraftwerk-harzenergie-am-14-1-2022/e1739715",
        )

        _assert_import_event(
            params,
            "eventbrite.html",
            "https://www.eventbrite.de/e/fr110322-wanderdate-sagenumwobene-brockentour-fur-singles-fur-40-65j-tickets-224906520457",
        )

        # None JSON
        with pytest.raises(Exception):
            _assert_import_event(
                params,
                "harzinfo_json_none.html",
                "https://www.harzinfo.de",
            )

        # With image
        utils.mock_image_request_with_file(
            "https://dam.destination.one/762032/f243062990392ce94607e37db3458303daedb6ce8b1aa03b80381f9b10aabc6b/210710-facebook-biathlon-challenge-2400x1256px-png.png",
            shared_datadir,
            "image500.png",
        )
        event = _assert_import_event(
            params,
            "harzinfo_biathlon.html",
            "https://www.harzinfo.de",
        )
        assert event is not None
        assert "lädt" in event.description
        assert event.photo is not None


def _assert_import_event(params, filename, url, sanitized_url=None):
    from project.services.importer.event_importer import EventImporter

    utils, admin_unit_id, datadir = params
    mock_url = sanitized_url if sanitized_url else url
    utils.mock_get_request_with_file(mock_url, datadir, filename)

    importer = EventImporter(admin_unit_id)
    event = importer.load_event_from_url(url)

    assert event is not None
    return event
