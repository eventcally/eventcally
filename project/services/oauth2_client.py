import time

from werkzeug.security import gen_salt

from project.models import OAuth2Client


def complete_oauth2_client(oauth2_client: OAuth2Client) -> None:
    if not oauth2_client.id:
        oauth2_client.client_id = gen_salt(24)
        oauth2_client.client_id_issued_at = int(time.time())

    if oauth2_client.client_secret is None:
        oauth2_client.client_secret = gen_salt(48)
