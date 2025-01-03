from flask import url_for
from flask_babel import gettext, lazy_gettext
from markupsafe import Markup

from project.modular.base_views import BaseListView


class ListView(BaseListView):
    def get_instruction(self, **kwargs):
        reference_open = "&quot;"
        reference_close = "&quot;"
        reference_title = gettext("Reference event")

        search_open = '<a href="%s">' % url_for("event_dates")
        search_close = "</a>"

        return Markup(
            lazy_gettext(
                "Here you can find events from other organizations that you referenced. To reference an event, select %(reference_open)s%(reference_title)s%(reference_close)s on an event page that you can find through the %(search_open)ssearch%(search_close)s.",
                reference_open=reference_open,
                reference_close=reference_close,
                reference_title=reference_title,
                search_open=search_open,
                search_close=search_close,
            )
        )
