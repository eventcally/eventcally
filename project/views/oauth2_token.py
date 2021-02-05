from project import app, db
from flask import render_template, redirect, flash, url_for
from flask_babelex import gettext
from flask_security import current_user
from project.models import OAuth2Token
from project.views.utils import (
    get_pagination_urls,
    handleSqlError,
    flash_errors,
)
from project.forms.oauth2_token import RevokeOAuth2TokenForm
from sqlalchemy.exc import SQLAlchemyError
from project.access import owner_access_or_401


@app.route("/oauth2_token/<int:id>/revoke", methods=("GET", "POST"))
def oauth2_token_revoke(id):
    oauth2_token = OAuth2Token.query.get_or_404(id)
    owner_access_or_401(oauth2_token.user_id)

    if oauth2_token.revoked:
        return redirect(url_for("oauth2_tokens"))

    form = RevokeOAuth2TokenForm()

    if form.validate_on_submit():
        try:
            oauth2_token.revoked = True
            db.session.commit()
            flash(gettext("OAuth2 token successfully revoked"), "success")
            return redirect(url_for("oauth2_tokens"))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(handleSqlError(e), "danger")
    else:
        flash_errors(form)

    return render_template(
        "oauth2_token/revoke.html", form=form, oauth2_token=oauth2_token
    )


@app.route("/oauth2_tokens")
def oauth2_tokens():
    oauth2_tokens = OAuth2Token.query.filter(
        OAuth2Token.user_id == current_user.id
    ).paginate()

    return render_template(
        "oauth2_token/list.html",
        oauth2_tokens=oauth2_tokens.items,
        pagination=get_pagination_urls(oauth2_tokens),
    )
