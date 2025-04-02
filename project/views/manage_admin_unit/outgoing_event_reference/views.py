from flask import g, url_for
from flask_babel import gettext, lazy_gettext
from markupsafe import Markup

from project.modular.base_views import BaseListView


class ListView(BaseListView):
    def get_instruction(self, **kwargs):
        reference_open = "&quot;"
        reference_close = "&quot;"
        reference_title = gettext("Request reference")

        search_open = '<a href="%s">' % url_for(
            "manage_admin_unit.events", id=g.manage_admin_unit.id
        )
        search_close = "</a>"

        return Markup(
            lazy_gettext(
                "Here you can find your events that are recommended by other organizations. To ask another organization for a recommendation, select %(reference_open)s%(reference_title)s%(reference_close)s on one of your event pages that you can find through the %(search_open)ssearch%(search_close)s.",
                reference_open=reference_open,
                reference_close=reference_close,
                reference_title=reference_title,
                search_open=search_open,
                search_close=search_close,
            )
        )
