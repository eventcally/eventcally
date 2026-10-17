from dependency_injector.wiring import Provide, inject
from flask import render_template, request

from project.application.queries import (
    GetOrganizationWidgetSettingsQuery,
    SearchEventDatesQuery,
)
from project.application.query_bus import QueryBus
from project.container import Application
from project.presentation.shared.query_results import (
    abort_if_page_out_of_range,
    page_request_from_request_args,
    result_or_404,
)
from project.presentation.web.forms.event_date import FindEventDateWidgetForm
from project.presentation.web.views.event import get_event_category_choices
from project.presentation.web.views.event_search_criteria import (
    criteria_from_search_params,
)
from project.presentation.web.views.event_search_params import EventSearchParams
from project.presentation.web.views.main_blueprint import main_bp
from project.presentation.web.views.utils import get_pagination_urls


@main_bp.route("/organizations/<int:id>/widget/eventdates")
@inject
def widget_event_dates(id, query_bus: QueryBus = Provide[Application.cqrs.query_bus]):
    admin_unit = result_or_404(
        query_bus.handle(GetOrganizationWidgetSettingsQuery(id=id))
    )

    params = EventSearchParams()
    params.set_default_date_range()

    form = FindEventDateWidgetForm(formdata=request.args, obj=params)
    form.category_id.choices = get_event_category_choices()
    form.category_id.choices.insert(0, (0, ""))

    if form.validate():
        form.populate_obj(params)

    params.admin_unit_id = admin_unit.id

    params.include_admin_unit_references = True
    dates = query_bus.handle(
        SearchEventDatesQuery(
            criteria=criteria_from_search_params(
                params, admin_unit_id=admin_unit.id, include_admin_unit_references=True
            ),
            page=page_request_from_request_args(),
        )
    )
    abort_if_page_out_of_range(dates)

    return render_template(
        "widget/event_date/list.html",
        form=form,
        styles=get_styles(admin_unit),
        admin_unit=admin_unit,
        params=params,
        dates=dates.items,
        pagination=get_pagination_urls(dates, id=id),
    )


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
