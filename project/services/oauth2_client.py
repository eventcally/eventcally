import time

from werkzeug.security import gen_salt

from project.models import AppKey, OAuth2Client


def complete_oauth2_client(oauth2_client: OAuth2Client) -> None:
    if not oauth2_client.id:
        oauth2_client.client_id = gen_salt(24)
        oauth2_client.client_id_issued_at = int(time.time())

    if oauth2_client.client_secret is None:
        oauth2_client.client_secret = gen_salt(48)


def add_keypair_to_oauth2_client(oauth2_client: OAuth2Client) -> tuple[bytes, AppKey]:
    app_key = AppKey()
    app_key.admin_unit_id = oauth2_client.admin_unit_id
    private_pem = app_key.generate_key()

    oauth2_client.app_keys.append(app_key)

    return (private_pem, app_key)
