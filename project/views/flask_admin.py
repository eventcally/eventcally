from flask import redirect, request, url_for
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_security import current_user

from project import app, db


class AuthAdminIndexView(AdminIndexView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.has_role("admin")


class AuthModelView(ModelView):
    can_view_details = True
    can_export = True
    column_display_pk = True
    column_display_all_relations = True
    column_hide_backrefs = False

    def _get_endpoint(self, endpoint):
        result = super()._get_endpoint(endpoint)
        return f"flask_admin_{result}"

    def is_accessible(self):
        return current_user.is_authenticated and current_user.has_role("admin")

    def inaccessible_callback(self, name, **kwargs):
        url = (
            url_for("security.login", next=request.url)
            if not current_user.is_authenticated
            else url_for("home")
        )
        return redirect(url)

    def __init__(self, model, session, **kwargs):
        super().__init__(model, session, **kwargs)

        if not self.column_filters:
            self._init_filters()

    def _init_filters(self):
        column_filters = list()
        for c in self._list_columns:
            flt = self.scaffold_filters(c[0])
            if flt:
                column_filters.extend(flt)
        self.column_filters = column_filters
        self._refresh_filters_cache()
        pass


admin = Admin(
    app,
    endpoint="flask_admin",
    index_view=AuthAdminIndexView(url="/admin/flask-admin", endpoint="flask_admin"),
    url="/admin/flask-admin",
    name=app.config["SITE_NAME"],
    template_mode="bootstrap4",
)


for mapper in db.Model.registry.mappers:
    class_ = mapper.class_
    if not class_:
        continue

    class CustomModelView(AuthModelView):
        column_list = [c_attr.key for c_attr in class_.__mapper__.column_attrs]

    admin.add_view(
        CustomModelView(
            class_,
            db.session,
            name=class_.get_display_name_plural(),
        )
    )
