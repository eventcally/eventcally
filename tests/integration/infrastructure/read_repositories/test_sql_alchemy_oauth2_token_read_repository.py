"""SqlAlchemyOAuth2TokenReadRepository against the database."""

from project.application.queries import ListUserOAuth2TokensQuery


def test_tokens_of_user(app, db, seeder):
    user_id, _ = seeder.setup_api_access()

    with app.app_context():
        from project.infrastructure.models import OAuth2Token

        token_id = OAuth2Token.query.filter(OAuth2Token.user_id == user_id).first().id
        repo = app.container.read_repos.oauth2_token_read_repo()

        with app.container.infrastructure.read_session_scope():
            page = repo.list(ListUserOAuth2TokensQuery(user_id=user_id))
            token = repo.get(token_id)
            missing = repo.get(4711)
            empty = repo.list(ListUserOAuth2TokensQuery(user_id=4711))

    assert [item.id for item in page.items] == [token_id]
    assert token.client_name == "Mein Client"
    assert token.user_id == user_id
    assert "openid" in token.scope
    assert token.expires_in > 0
    assert not token.is_revoked()
    assert missing is None
    assert empty.total == 0
