from flask_security import auth_required

from project.presentation.web.modular.base_view_handler import BaseViewHandler


class ManageChildViewHandler(BaseViewHandler):
    decorators = [auth_required()]
