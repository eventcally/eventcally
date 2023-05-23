from authlib.integrations.flask_oauth2 import AuthorizationServer, ResourceProtector
from authlib.integrations.sqla_oauth2 import (
    create_bearer_token_validator,
    create_query_client_func,
    create_query_token_func,
    create_save_token_func,
)
from authlib.oauth2.rfc6749 import grants
from authlib.oauth2.rfc7636 import CodeChallenge
from authlib.oauth2.rfc7662 import IntrospectionEndpoint
from authlib.oidc.core import UserInfo
from authlib.oidc.core.grants import OpenIDCode as _OpenIDCode
from flask import url_for

from project import app, db
from project.models import OAuth2AuthorizationCode, OAuth2Client, OAuth2Token, User


def get_issuer():
    return url_for("home", _external=True).rstrip("/")


def generate_user_info(user, scope):
    return UserInfo(sub=str(user.id), email=user.email)


def exists_nonce(nonce, request):
    exists = OAuth2AuthorizationCode.query.filter_by(
        client_id=request.client_id, nonce=nonce
    ).first()
    return bool(exists)


class AuthorizationCodeGrant(grants.AuthorizationCodeGrant):
    TOKEN_ENDPOINT_AUTH_METHODS = [
        "client_secret_basic",
        "client_secret_post",
        "none",
    ]

    def save_authorization_code(self, code, request):
        code_challenge = request.data.get("code_challenge")
        code_challenge_method = request.data.get("code_challenge_method")
        nonce = request.data.get("nonce")
        auth_code = OAuth2AuthorizationCode(
            code=code,
            client_id=request.client.client_id,
            redirect_uri=request.redirect_uri,
            scope=request.scope,
            user_id=request.user.id,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method,
            nonce=nonce,
        )
        db.session.add(auth_code)
        db.session.commit()
        return auth_code

    def query_authorization_code(self, code, client):
        auth_code = OAuth2AuthorizationCode.query.filter_by(
            code=code, client_id=client.client_id
        ).first()
        if auth_code and not auth_code.is_expired():
            return auth_code

    def delete_authorization_code(self, authorization_code):
        db.session.delete(authorization_code)
        db.session.commit()

    def authenticate_user(self, authorization_code):
        return db.session.get(User, authorization_code.user_id)


class ClientCredentialsGrant(grants.ClientCredentialsGrant):
    TOKEN_ENDPOINT_AUTH_METHODS = ["client_secret_basic", "client_secret_post"]


class OpenIDCode(_OpenIDCode):
    def exists_nonce(self, nonce, request):
        return exists_nonce(nonce, request)

    def get_jwt_config(self, grant):
        return {
            "key": app.config["JWT_PRIVATE_KEY"],
            "alg": "RS256",
            "iss": get_issuer(),
            "exp": 3600,
        }

    def generate_user_info(self, user, scope):
        return generate_user_info(user, scope)


class RefreshTokenGrant(grants.RefreshTokenGrant):
    TOKEN_ENDPOINT_AUTH_METHODS = ["client_secret_basic", "client_secret_post"]
    INCLUDE_NEW_REFRESH_TOKEN = True

    def authenticate_refresh_token(self, refresh_token):
        token = OAuth2Token.query.filter_by(refresh_token=refresh_token).first()
        if token and token.is_refresh_token_active():
            return token

    def authenticate_user(self, credential):
        return db.session.get(User, credential.user_id)

    def revoke_old_credential(self, credential):
        credential.revoked = True
        db.session.add(credential)
        db.session.commit()


class MyIntrospectionEndpoint(IntrospectionEndpoint):
    CLIENT_AUTH_METHODS = ["client_secret_basic", "client_secret_post"]

    def query_token(self, token_string, token_type_hint):
        if token_type_hint == "access_token":
            tok = OAuth2Token.query.filter_by(access_token=token_string).first()
        elif token_type_hint == "refresh_token":
            tok = OAuth2Token.query.filter_by(refresh_token=token_string).first()
        else:
            # without token_type_hint
            tok = OAuth2Token.query.filter_by(access_token=token_string).first()
            if not tok:
                tok = OAuth2Token.query.filter_by(refresh_token=token_string).first()

        return tok

    def check_permission(self, token, client, request):
        return token.client_id == client.client_id

    def introspect_token(self, token):
        return {
            "active": True,
            "client_id": token.client_id,
            "token_type": token.token_type,
            "username": token.user.email,
            "scope": token.get_scope(),
            "sub": str(token.user.id),
            "aud": token.client_id,
            "iss": get_issuer(),
            "exp": token.expires_at,
            "iat": token.issued_at,
        }


query_client = create_query_client_func(db.session, OAuth2Client)
save_token = create_save_token_func(db.session, OAuth2Token)
authorization = AuthorizationServer(
    query_client=query_client,
    save_token=save_token,
)
require_oauth = ResourceProtector()


def create_revocation_endpoint(session, token_model):
    from authlib.oauth2.rfc7009 import RevocationEndpoint

    query_token = create_query_token_func(session, token_model)

    class _RevocationEndpoint(RevocationEndpoint):
        CLIENT_AUTH_METHODS = ["client_secret_basic", "client_secret_post"]

        def query_token(self, token_string, token_type_hint):
            return query_token(token_string, token_type_hint)

        def revoke_token(self, token, request):
            token.revoke_token()
            session.add(token)
            session.commit()

    return _RevocationEndpoint


def config_oauth(app):
    app.config["OAUTH2_REFRESH_TOKEN_GENERATOR"] = True
    authorization.init_app(app)

    # support grants
    authorization.register_grant(
        AuthorizationCodeGrant,
        [CodeChallenge(required=True), OpenIDCode()],
    )
    authorization.register_grant(ClientCredentialsGrant)
    authorization.register_grant(RefreshTokenGrant)

    # support revocation
    revocation_cls = create_revocation_endpoint(db.session, OAuth2Token)
    authorization.register_endpoint(revocation_cls)

    # support introspect
    authorization.register_endpoint(MyIntrospectionEndpoint)

    # protect resource
    bearer_cls = create_bearer_token_validator(db.session, OAuth2Token)
    require_oauth.register_token_validator(bearer_cls())
