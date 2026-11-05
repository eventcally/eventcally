from typing import Callable

from flask import abort, current_app, render_template

from project.application.query_bus import QueryBus
from project.presentation.shared.access import admin_unit_owner_access_or_401
from project.presentation.web.boot import build_boot_data


def render_manage_shell(title, **context):
    """The Vue 3 frame of the `manage` entry; the page reads and writes via `/bff/manage`."""
    return render_template(
        "manage/shell.html",
        entry="manage",
        title=title,
        boot=build_boot_data(base="/"),
        **context,
    )


def query_bus() -> QueryBus:
    return current_app.container.cqrs.query_bus()


def owned_object_or_abort(
    query,
    admin_unit_id_of: Callable = lambda object: object.admin_unit_id,
):
    """The object of a shell's URL: 404 when it does not exist, 401 when it belongs to
    another organization than the one the user manages."""
    object = query_bus().handle(query)

    if object is None:
        abort(404)

    admin_unit_owner_access_or_401(admin_unit_id_of(object))
    return object
