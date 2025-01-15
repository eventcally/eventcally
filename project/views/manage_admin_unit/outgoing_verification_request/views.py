from project.modular.base_views import BaseListView
from project.views import utils


class ListView(BaseListView):
    def get_docs_url(self, **kwargs):  # pragma: no cover
        return utils.get_docs_url("/goto/organization-verify", **kwargs)
