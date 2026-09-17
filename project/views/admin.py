from dependency_injector.wiring import Provide, inject
from flask import current_app, flash, redirect, render_template, request, url_for
from flask_babel import gettext
from flask_security import roles_required
from sqlalchemy.sql import func

from project.application.commands import (
    DeleteUserCommand,
    ResetTosAcceptedForUsersCommand,
    UpdatePlanningSettingsCommand,
    UpdateSettingsCommand,
    UpdateUserRolesCommand,
)
from project.application.message_bus import MessageBus
from project.container import Application
from project.domain.errors import BaseError
from project.forms.admin import (
    AdminNewsletterForm,
    AdminPlanningForm,
    AdminSettingsForm,
    AdminTestEmailForm,
    DeleteUserForm,
    ResetTosAceptedForm,
    UpdateUserForm,
)
from project.models import Role, User
from project.services.admin import upsert_settings
from project.views.admin_blueprint import admin_bp
from project.views.utils import (
    flash_errors,
    get_celery_poll_group_result,
    get_pagination_urls,
    handleBaseError,
    non_match_for_deletion,
    send_template_mail,
    send_template_mail_async,
    send_template_mails_to_users_async,
)


@admin_bp.route("/reset-tos-accepted", methods=("GET", "POST"))
@roles_required("admin")
@inject
def admin_reset_tos_accepted(
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
):
    form = ResetTosAceptedForm()

    if form.validate_on_submit():
        try:
            cmd = ResetTosAcceptedForUsersCommand(
                actor=current_app.container.context.context_provider().current_actor
            )
            message_bus.handle_command(cmd)
            return redirect(url_for("admin.admin"))
        except BaseError as e:
            flash(handleBaseError(e), "danger")
    else:
        flash_errors(form)

    return render_template("admin/reset_tos_accepted.html", form=form)


@admin_bp.route("/settings", methods=("GET", "POST"))
@roles_required("admin")
@inject
def admin_settings(message_bus: MessageBus = Provide[Application.cqrs.message_bus]):
    settings = upsert_settings()
    form = AdminSettingsForm(obj=settings)

    if form.validate_on_submit():
        try:
            cmd = UpdateSettingsCommand(
                actor=current_app.container.context.context_provider().current_actor,
                tos=form.tos.data,
                legal_notice=form.legal_notice.data,
                contact=form.contact.data,
                privacy=form.privacy.data,
                start_page=form.start_page.data,
                announcement=form.announcement.data,
            )
            message_bus.handle_command(cmd)
            flash(gettext("Settings successfully updated"), "success")
            return redirect(url_for("admin.admin"))
        except BaseError as e:
            flash(handleBaseError(e), "danger")
    else:
        flash_errors(form)

    return render_template("admin/settings.html", form=form)


@admin_bp.route("/email", methods=["GET", "POST"])
@roles_required("admin")
def admin_email():
    form = AdminTestEmailForm()

    if "poll" in request.args:  # pragma: no cover
        return get_celery_poll_group_result()

    if form.validate_on_submit():
        template = "test_email"
        context = {"site_name": current_app.config["SITE_NAME"]}

        if "async" in request.args:  # pragma: no cover
            result = send_template_mail_async(form.recipient.data, template, **context)
            result.save()
            return {"result_id": result.id}

        try:
            send_template_mail(form.recipient.data, template, **context)
            flash(gettext("Mail sent successfully"), "success")
        except Exception as e:  # pragma: no cover
            flash(str(e), "danger")
    else:  # pragma: no cover
        flash_errors(form)

    return render_template("admin/email.html", form=form)


@admin_bp.route("/newsletter", methods=["GET", "POST"])
@roles_required("admin")
def admin_newsletter():
    form = AdminNewsletterForm()

    if "poll" in request.args:  # pragma: no cover
        return get_celery_poll_group_result()

    if form.validate_on_submit():
        template = "newsletter"
        context = {
            "site_name": current_app.config["SITE_NAME"],
            "message": form.message.data,
        }

        if form.recipient_choice.data == 1:  # pragma: no cover
            result = send_template_mail_async(
                form.test_recipient.data,
                template,
                **context,
            )
        else:
            users = (
                User.query.filter(User.email != None)
                .filter(User.confirmed_at != None)
                .filter(User.newsletter_enabled)
                .all()
            )
            result = send_template_mails_to_users_async(
                users,
                template,
                **context,
            )

        result.save()
        return {"result_id": result.id}

    return render_template("admin/newsletter.html", form=form)


@admin_bp.route("/users")
@roles_required("admin")
def admin_users():
    users = User.query.order_by(func.lower(User.email)).paginate()
    return render_template(
        "admin/users.html", users=users.items, pagination=get_pagination_urls(users)
    )


@admin_bp.route("/user/<int:id>/update", methods=("GET", "POST"))
@roles_required("admin")
@inject
def admin_user_update(
    id, message_bus: MessageBus = Provide[Application.cqrs.message_bus]
):
    user = User.query.get_or_404(id)

    form = UpdateUserForm()
    form.roles.choices = [
        (c.name, gettext(c.title)) for c in Role.query.order_by(Role.id).all()
    ]

    if form.validate_on_submit():
        try:
            cmd = UpdateUserRolesCommand(
                actor=current_app.container.context.context_provider().current_actor,
                id=user.id,
                roles=form.roles.data,
            )
            message_bus.handle_command(cmd)
            flash(gettext("User successfully updated"), "success")
            return redirect(url_for("admin.admin_users"))
        except BaseError as e:
            flash(handleBaseError(e), "danger")
    else:
        form.roles.data = [c.name for c in user.roles]

    return render_template("admin/update_user.html", user=user, form=form)


@admin_bp.route("/user/<int:id>/delete", methods=("GET", "POST"))
@roles_required("admin")
@inject
def admin_user_delete(
    id, message_bus: MessageBus = Provide[Application.cqrs.message_bus]
):
    user = User.query.get_or_404(id)

    form = DeleteUserForm()

    if form.validate_on_submit():
        if non_match_for_deletion(form.email.data, user.email):
            flash(gettext("Entered email does not match user email"), "danger")
        else:
            try:
                cmd = DeleteUserCommand(
                    actor=current_app.container.context.context_provider().current_actor,
                    id=user.id,
                )
                message_bus.handle_command(cmd)
                flash(gettext("User successfully deleted"), "success")
                return redirect(url_for("admin.admin_users"))
            except BaseError as e:
                flash(handleBaseError(e), "danger")
    else:
        flash_errors(form)

    return render_template("admin/delete_user.html", form=form, user=user)


@admin_bp.route("/planning", methods=("GET", "POST"))
@roles_required("admin")
@inject
def admin_planning(message_bus: MessageBus = Provide[Application.cqrs.message_bus]):
    settings = upsert_settings()
    form = AdminPlanningForm(obj=settings)

    if form.validate_on_submit():
        try:
            cmd = UpdatePlanningSettingsCommand(
                actor=current_app.container.context.context_provider().current_actor,
                planning_external_calendars=form.planning_external_calendars.data,
            )
            message_bus.handle_command(cmd)
            flash(gettext("Settings successfully updated"), "success")
            return redirect(url_for("admin.admin"))
        except BaseError as e:
            flash(handleBaseError(e), "danger")
    else:
        flash_errors(form)

    return render_template("admin/planning.html", form=form)
