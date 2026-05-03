from authlib.integrations.flask_oauth2 import current_token
from authlib.oauth2 import OAuth2Error
from flask import current_app, jsonify, redirect, render_template, request, url_for
from flask_security import current_user

from project.api import scope_list, scopes
from project.forms.security import AuthorizeForm
from project.oauth2 import generate_user_info, get_issuer
from project.oauth2_extensions import authorization, require_oauth
from project.views.main_blueprint import main_bp


@main_bp.route("/oauth/authorize", methods=["GET", "POST"])
def authorize():
    user = current_user

    if not user or not user.is_authenticated:
        return redirect(url_for("security.login", next=request.url))

    form = AuthorizeForm()

    if form.validate_on_submit():
        grant_user = user if form.allow.data else None
        return authorization.create_authorization_response(grant_user=grant_user)
    else:
        try:
            grant = authorization.get_consent_grant(end_user=user)
        except OAuth2Error as error:
            return error.description, error.status_code

        grant_scopes = grant.request.scope.split(" ") if grant.request.scope else []
        filtered_scopes = {k: scopes[k] for k in grant_scopes if k in scopes}
        return render_template(
            "security/authorize.html",
            form=form,
            scopes=filtered_scopes,
            user=user,
            grant=grant,
        )


@main_bp.route("/oauth/token", methods=["POST"])
def issue_token():
    return authorization.create_token_response()


@main_bp.route("/oauth/revoke", methods=["POST"])
def revoke_token():
    return authorization.create_endpoint_response("revocation")


@main_bp.route("/oauth/introspect", methods=["POST"])
def introspect():
    return authorization.create_endpoint_response("introspection")


@main_bp.route("/oauth2-redirect.html")
def swagger_oauth2_redirect():
    return redirect(
        url_for("flask-apispec.static", filename="oauth2-redirect.html", **request.args)
    )


@main_bp.route("/oauth/userinfo")
@require_oauth("profile")
def oauth_userinfo():
    return jsonify(generate_user_info(current_token.user, current_token.scope))


@main_bp.route("/.well-known/jwks.json")
def jwks():
    response = current_app.response_class(
        response=current_app.config["JWT_PUBLIC_JWKS"],
        status=200,
        mimetype="application/json",
    )
    return response


@main_bp.route("/.well-known/openid-configuration")
def openid_configuration():
    c = dict()
    c["issuer"] = get_issuer()
    c["authorization_endpoint"] = url_for("main.authorize", _external=True)
    c["token_endpoint"] = url_for("main.issue_token", _external=True)
    c["userinfo_endpoint"] = url_for("main.oauth_userinfo", _external=True)
    c["revocation_endpoint"] = url_for("main.revoke_token", _external=True)
    c["introspection_endpoint"] = url_for("main.introspect", _external=True)
    c["jwks_uri"] = url_for("main.jwks", _external=True)
    c["scopes_supported"] = scope_list
    c["token_endpoint_auth_methods_supported"] = [
        "client_secret_post",
        "client_secret_basic",
    ]
    c["claims_supported"] = [
        "username",
        "sub",
        "aud",
        "iss",
        "exp",
        "iat",
    ]
    c["response_types_supported"] = ["code", "id_token", "token id_token"]
    c["grant_types_supported"] = [
        "authorization_code",
        "refresh_token",
    ]
    return jsonify(c)
