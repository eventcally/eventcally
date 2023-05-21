from flask import flash, redirect, render_template, url_for
from flask_babel import gettext
from flask_security import current_user
from sqlalchemy.exc import SQLAlchemyError

from project import app, db
from project.access import owner_access_or_401
from project.forms.oauth2_client import (
    CreateOAuth2ClientForm,
    DeleteOAuth2ClientForm,
    UpdateOAuth2ClientForm,
)
from project.models import OAuth2Client
from project.services.oauth2_client import complete_oauth2_client
from project.views.utils import (
    flash_errors,
    get_pagination_urls,
    handleSqlError,
    non_match_for_deletion,
)


@app.route("/oauth2_client/create", methods=("GET", "POST"))
def oauth2_client_create():
    form = CreateOAuth2ClientForm()

    if form.validate_on_submit():
        oauth2_client = OAuth2Client()
        form.populate_obj(oauth2_client)
        oauth2_client.user_id = current_user.id
        complete_oauth2_client(oauth2_client)

        try:
            db.session.add(oauth2_client)
            db.session.commit()
            flash(gettext("OAuth2 client successfully created"), "success")
            return redirect(url_for("oauth2_client", id=oauth2_client.id))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(handleSqlError(e), "danger")
    else:
        flash_errors(form)

    return render_template("oauth2_client/create.html", form=form)


@app.route("/oauth2_client/<int:id>/update", methods=("GET", "POST"))
def oauth2_client_update(id):
    oauth2_client = OAuth2Client.query.get_or_404(id)
    owner_access_or_401(oauth2_client.user_id)

    form = UpdateOAuth2ClientForm(obj=oauth2_client)

    if form.validate_on_submit():
        form.populate_obj(oauth2_client)
        complete_oauth2_client(oauth2_client)

        try:
            db.session.commit()
            flash(gettext("OAuth2 client successfully updated"), "success")
            return redirect(url_for("oauth2_client", id=oauth2_client.id))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(handleSqlError(e), "danger")
    else:
        flash_errors(form)

    return render_template(
        "oauth2_client/update.html", form=form, oauth2_client=oauth2_client
    )


@app.route("/oauth2_client/<int:id>/delete", methods=("GET", "POST"))
def oauth2_client_delete(id):
    oauth2_client = OAuth2Client.query.get_or_404(id)
    owner_access_or_401(oauth2_client.user_id)

    form = DeleteOAuth2ClientForm()

    if form.validate_on_submit():
        if non_match_for_deletion(form.name.data, oauth2_client.client_name):
            flash(gettext("Entered name does not match OAuth2 client name"), "danger")
        else:
            try:
                db.session.delete(oauth2_client)
                db.session.commit()
                flash(gettext("OAuth2 client successfully deleted"), "success")
                return redirect(url_for("oauth2_clients"))
            except SQLAlchemyError as e:
                db.session.rollback()
                flash(handleSqlError(e), "danger")
    else:
        flash_errors(form)

    return render_template(
        "oauth2_client/delete.html", form=form, oauth2_client=oauth2_client
    )


@app.route("/oauth2_client/<int:id>")
def oauth2_client(id):
    oauth2_client = OAuth2Client.query.get_or_404(id)
    owner_access_or_401(oauth2_client.user_id)

    return render_template(
        "oauth2_client/read.html",
        oauth2_client=oauth2_client,
    )


@app.route("/oauth2_clients")
def oauth2_clients():
    oauth2_clients = (
        OAuth2Client.query.filter(OAuth2Client.user_id == current_user.id)
        .order_by(OAuth2Client.id)
        .paginate()
    )

    return render_template(
        "oauth2_client/list.html",
        oauth2_clients=oauth2_clients.items,
        pagination=get_pagination_urls(oauth2_clients),
    )
