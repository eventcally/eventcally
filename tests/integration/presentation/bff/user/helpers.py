"""Shared helpers of the `/bff/user` tests."""


def shell(utils):
    """Loads a user shell: it carries the CSRF token for the writes."""
    utils.get_ok("/profile")


def flashes(client):
    with client.session_transaction() as session:
        return [(category, str(message)) for category, message in session["_flashes"]]
