def _first_token(app):
    from project.infrastructure.models import OAuth2Token

    return OAuth2Token.query.first()


def test_token_properties_and_labels(app, db, seeder):
    seeder.setup_api_access()

    with app.app_context():
        token = _first_token(app)

        assert token.expires_at == token.issued_at + token.expires_in
        assert token.expires_at_datetime.timestamp() == token.expires_at
        assert token.issued_at_datetime.timestamp() == token.issued_at
        assert token.client_name == token.client.client_name
        assert str(token).endswith(f"({token.client.client_name})")


def test_rate_limit_key_includes_the_user(app, db, seeder):
    seeder.setup_api_access()

    with app.app_context():
        token = _first_token(app)
        client_key = token.client.get_rate_limit_key()

        assert token.user_id
        assert token.get_rate_limit_key() == f"{client_key}-{token.user_id}"
        assert token.get_rate_limit_value() == token.client.rate_limit_value

        token.user_id = None

        assert token.get_rate_limit_key() == client_key


def test_revoked_token_has_no_active_refresh_token(app, db, seeder):
    seeder.setup_api_access()

    with app.app_context():
        token = _first_token(app)
        assert token.is_refresh_token_active()

        token.revoke_token()

        assert token.is_revoked()
        assert not token.is_refresh_token_active()


def test_client_is_looked_up_once(app, db, seeder):
    import sqlalchemy

    seeder.setup_api_access()

    with app.app_context():
        token = _first_token(app)
        client = token.client
        queries = []

        def _count(*args, **kwargs):
            queries.append(args)

        sqlalchemy.event.listen(db.engine, "before_cursor_execute", _count)
        try:
            assert token.client is client
        finally:
            sqlalchemy.event.remove(db.engine, "before_cursor_execute", _count)

        assert queries == []
