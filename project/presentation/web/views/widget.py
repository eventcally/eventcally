from types import SimpleNamespace

from dependency_injector.wiring import Provide, inject
from flask import render_template, request

from project.application.queries import (
    GetOrganizationWidgetSettingsQuery,
    SearchEventDatesQuery,
)
from project.application.query_bus import QueryBus
from project.container import Application
from project.presentation.shared.legacy_widget_search import legacy_widget_criteria
from project.presentation.shared.query_results import (
    abort_if_page_out_of_range,
    page_request_from_request_args,
    result_or_404,
)
from project.presentation.web.boot import build_boot_data
from project.presentation.web.views.main_blueprint import main_bp


# The URL and the endpoint name are a contract: customers embed this page in an iframe
# (the endpoint name is exempt from X-Frame-Options in requests.py). The page is a Vue
# shell; it reads through /bff/public/widget/organizations/<id>/event-dates.
@main_bp.route("/organizations/<int:id>/widget/eventdates")
@inject
def widget_event_dates(id, query_bus: QueryBus = Provide[Application.cqrs.query_bus]):
    admin_unit = result_or_404(
        query_bus.handle(GetOrganizationWidgetSettingsQuery(id=id))
    )

    # The status codes of the document stay what they were: 404 for a bad or an
    # out-of-range page, before the shell renders.
    page_request = page_request_from_request_args()
    filters = SimpleNamespace(
        **{
            name: request.args.get(name)
            for name in ("date_from", "date_to", "keyword", "category_id", "tag")
        }
    )
    dates = query_bus.handle(
        SearchEventDatesQuery(
            criteria=legacy_widget_criteria(query_bus, admin_unit.id, filters),
            page=page_request,
        )
    )
    abort_if_page_out_of_range(dates)

    boot = build_boot_data(base="/")
    boot["widget"] = {
        "organizationId": admin_unit.id,
        "settings": get_settings(admin_unit, page_request.per_page),
    }
    return render_template("widget/event_dates.html", boot=boot)


def get_settings(admin_unit, per_page):
    """The page's settings in the keys of the custom search widget. The colors of the
    request (`s_*`, as `widget-loader.js` sends them) win over the stored ones; only what
    is set is styled."""
    styles = get_styles(admin_unit)
    settings = {
        "layout": "card",
        "organizationId": admin_unit.id,
        "eventsPerPage": per_page,
        "showFilter": True,
        "showPagination": True,
        "showPrintButton": True,
        "showEventCallyLink": False,
        # The cards of the old page were transparent.
        "eventBackgroundColor": "transparent",
    }

    if "font" in styles:
        settings["fontFamily"] = styles["font"]

    if "background" in styles:
        settings["background"] = styles["background"]

    if "primary" in styles:
        settings["buttonBackgroundColor"] = styles["primary"]
        settings["buttonBorderColor"] = styles["primary"]

    if "link" in styles:
        settings["linkColor"] = styles["link"]
        settings["eventNameTextColor"] = styles["link"]
        settings["pagingColor"] = styles["link"]

    return settings


def get_styles(admin_unit):
    styles = dict()

    if request.args.get("s_ft", None):
        styles["font"] = request.args["s_ft"]
    elif admin_unit.widget_font:
        styles["font"] = admin_unit.widget_font

    if request.args.get("s_bg", None):
        styles["background"] = request.args["s_bg"]
    elif admin_unit.widget_background_color:
        styles["background"] = admin_unit.widget_background_color

    if request.args.get("s_pr", None):
        styles["primary"] = request.args["s_pr"]
    elif admin_unit.widget_primary_color:
        styles["primary"] = admin_unit.widget_primary_color

    if request.args.get("s_li", None):
        styles["link"] = request.args["s_li"]
    elif admin_unit.widget_link_color:
        styles["link"] = admin_unit.widget_link_color

    return styles
