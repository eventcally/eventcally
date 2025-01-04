from flask import g, url_for
from flask_babel import gettext, lazy_gettext
from markupsafe import Markup

from project.modular.base_views import BaseListView


class ListView(BaseListView):
    def get_instruction(self, **kwargs):
        request_open = "&quot;"
        request_close = "&quot;"
        request_title = gettext("Request reference")

        search_open = '<a href="%s">' % url_for(
            "manage_admin_unit_events", id=g.manage_admin_unit.id
        )
        search_close = "</a>"

        return Markup(
            lazy_gettext(
                "Here you can find your recommendation requests to other organizations. To ask another organization for a recommendation, select %(request_open)s%(request_title)s%(request_close)s on one of your event pages that you can find through the %(search_open)ssearch%(search_close)s.",
                request_open=request_open,
                request_close=request_close,
                request_title=request_title,
                search_open=search_open,
                search_close=search_close,
            )
        )
