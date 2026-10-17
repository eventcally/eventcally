from flask_security import auth_required

from project.views.modular.base_view_handler import BaseViewHandler


class ManageChildViewHandler(BaseViewHandler):
    decorators = [auth_required()]
