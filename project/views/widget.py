from flask import render_template, request

from project import app
from project.forms.event_date import FindEventDateWidgetForm
from project.models import AdminUnit
from project.services.event import get_event_dates_query
from project.services.search_params import EventSearchParams
from project.views.event import get_event_category_choices
from project.views.utils import get_pagination_urls


@app.route("/organizations/<int:id>/widget/eventdates")
def widget_event_dates(id):
    admin_unit = AdminUnit.query.get_or_404(id)

    params = EventSearchParams()
    params.set_default_date_range()

    form = FindEventDateWidgetForm(formdata=request.args, obj=params)
    form.category_id.choices = get_event_category_choices()
    form.category_id.choices.insert(0, (0, ""))

    if form.validate():
        form.populate_obj(params)

    if not params.event_list_id:
        params.admin_unit_id = admin_unit.id

    params.include_admin_unit_references = True
    dates = get_event_dates_query(params).paginate()

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
        styles["background"] = admin_unit.widget_background_color.hex

    if request.args.get("s_pr", None):
        styles["primary"] = request.args["s_pr"]
    elif admin_unit.widget_primary_color:
        styles["primary"] = admin_unit.widget_primary_color.hex

    if request.args.get("s_li", None):
        styles["link"] = request.args["s_li"]
    elif admin_unit.widget_link_color:
        styles["link"] = admin_unit.widget_link_color.hex

    return styles
