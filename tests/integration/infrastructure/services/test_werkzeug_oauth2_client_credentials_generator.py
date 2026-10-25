from project.infrastructure.services.werkzeug_oauth2_client_credentials_generator import (
    WerkzeugOAuth2ClientCredentialsGenerator,
)


def test_generate_returns_client_id_and_longer_secret():
    client_id, client_secret = WerkzeugOAuth2ClientCredentialsGenerator().generate()

    assert len(client_id) == 24
    assert len(client_secret) == 48
