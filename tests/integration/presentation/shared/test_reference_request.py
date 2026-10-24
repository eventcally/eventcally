from project.presentation.shared.reference_request import (
    get_success_text_for_request_creation,
)


def test_success_text_of_a_verified_request(app):
    with app.test_request_context():
        assert (
            get_success_text_for_request_creation("Crew", True)
            == "Crew hat deine Empfehlungsanfrage akzeptiert"
        )


def test_success_text_of_an_open_request(app):
    with app.test_request_context():
        text = get_success_text_for_request_creation("Crew", False)

    assert text.startswith("Empfehlungsanfrage an Crew erfolgreich erstellt.")
