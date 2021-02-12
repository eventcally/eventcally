from authlib.oauth2 import OAuth2Error
from flask import redirect, render_template, request, url_for
from flask_security import current_user

from project import app
from project.api import scopes
from project.forms.security import AuthorizeForm
from project.oauth2 import authorization


@app.route("/oauth/authorize", methods=["GET", "POST"])
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
            grant = authorization.validate_consent_request(end_user=user)
        except OAuth2Error as error:
            return error.error

        grant_scopes = grant.request.scope.split(" ")
        filtered_scopes = {k: scopes[k] for k in grant_scopes}
        return render_template(
            "security/authorize.html",
            form=form,
            scopes=filtered_scopes,
            user=user,
            grant=grant,
        )


@app.route("/oauth/token", methods=["POST"])
def issue_token():
    return authorization.create_token_response()


@app.route("/oauth/revoke", methods=["POST"])
def revoke_token():
    return authorization.create_endpoint_response("revocation")


@app.route("/oauth2-redirect.html")
def swagger_oauth2_redirect():
    return redirect(
        url_for("flask-apispec.static", filename="oauth2-redirect.html", **request.args)
    )
