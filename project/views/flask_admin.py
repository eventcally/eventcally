from flask import flash, redirect, request, url_for
from flask_admin import Admin, AdminIndexView, BaseView, expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.model.template import EndpointLinkRowAction
from flask_babel import lazy_gettext
from flask_security import current_user
from sqlalchemy.ext.hybrid import hybrid_property

from project import app, db
from project.models.admin_unit import AdminUnit
from project.models.event_place import EventPlace
from project.models.user import User


class AuthAdminIndexView(AdminIndexView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.has_role("admin")


class AuthBaseView(BaseView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.has_role("admin")


class AuthModelView(ModelView):
    can_view_details = True
    can_export = True
    column_display_pk = True
    column_display_all_relations = True
    column_hide_backrefs = False
    named_filter_urls = True
    can_set_page_size = True

    def _get_endpoint(self, endpoint):
        result = super()._get_endpoint(endpoint)
        return f"flask_admin_{self.__class__.__name__.lower()}_{result}"

    def is_accessible(self):
        return current_user.is_authenticated and current_user.has_role("admin")

    def inaccessible_callback(self, name, **kwargs):
        url = (
            url_for("security.login", next=request.url)
            if not current_user.is_authenticated
            else url_for("home")
        )
        return redirect(url)

    def scaffold_list_columns(self):
        columns = super().scaffold_list_columns()

        for c_attr in self.model.__mapper__.column_attrs:
            if c_attr.key not in columns:
                columns.append(c_attr.key)

        for (
            descriptor_key,
            descriptor,
        ) in self.model.__mapper__.all_orm_descriptors.items():
            if (
                isinstance(descriptor, hybrid_property)
                and descriptor_key not in columns
            ):
                try:
                    getattr(self.model, descriptor_key)
                except NotImplementedError:
                    continue
                columns.append(descriptor_key)

        if self.model.__tablename__ == "image":
            columns.remove("data")

        if self.model.__tablename__ == "role":
            columns.remove("users")

        if self.model.__tablename__ == "adminunitmemberrole":
            columns.remove("members")

        return columns

    def get_filters(self):
        if not self.column_filters:
            column_filters = list()
            for c in self._list_columns:
                flt = self.scaffold_filters(c[0])
                if flt:
                    column_filters.extend(flt)
            self.column_filters = column_filters

        return super().get_filters()


class OrganizationView(AuthModelView):
    column_list = (
        AdminUnit.name,
        AdminUnit.is_verified,
        AdminUnit.incoming_reference_requests_allowed,
        AdminUnit.can_create_other,
        AdminUnit.can_invite_other,
        AdminUnit.can_verify_other,
        AdminUnit.created_at,
        AdminUnit.deletion_requested_at,
    )
    column_filters = (
        AdminUnit.name,
        "is_verified",
        AdminUnit.incoming_reference_requests_allowed,
        AdminUnit.can_create_other,
        AdminUnit.can_invite_other,
        AdminUnit.can_verify_other,
        AdminUnit.created_at,
        AdminUnit.deletion_requested_at,
    )
    column_searchable_list = (AdminUnit.name,)
    column_default_sort = "name"
    form_columns = (
        AdminUnit.incoming_reference_requests_allowed,
        AdminUnit.can_create_other,
        AdminUnit.can_invite_other,
        AdminUnit.can_verify_other,
    )
    edit_modal = True
    column_extra_row_actions = [
        EndpointLinkRowAction("fa fa-eye", "manage_admin_unit", lazy_gettext("Manage")),
        EndpointLinkRowAction(
            "fa fa-eye", "organizations", lazy_gettext("View"), "path"
        ),
    ]


class UserView(AuthModelView):
    column_list = (
        User.email,
        User.created_at,
        User.confirmed_at,
        User.deletion_requested_at,
        User.active,
        User.tos_accepted_at,
        User.locale,
    )
    column_filters = (
        User.email,
        User.created_at,
        User.confirmed_at,
        User.deletion_requested_at,
        User.active,
        User.tos_accepted_at,
        User.locale,
    )
    column_searchable_list = (User.email,)
    column_default_sort = "email"
    form_columns = (
        "roles",
        User.active,
        User.confirmed_at,
        User.deletion_requested_at,
        User.tos_accepted_at,
        User.locale,
    )
    edit_modal = True


class EventPlaceView(AuthModelView):
    column_list = (
        EventPlace.name,
        "location",
    )
    column_searchable_list = (EventPlace.name,)
    column_default_sort = "name"


class CustomCategoryExtensionView(AuthBaseView):
    @expose("/", methods=["GET", "POST"])
    def index(self):
        if request.method == "POST":
            file = request.files.get("file")
            if not file:
                flash("No file uploaded", "error")
                return redirect(request.url)

            try:
                import json

                from project.models import CustomEventCategory, CustomEventCategorySet

                category_set_id = request.form.get("category_set_id")
                category_set = db.session.get(CustomEventCategorySet, category_set_id)

                if not category_set:
                    flash(
                        f"Category set with {category_set_id} does not exist",
                        "error",
                    )
                    return redirect(request.url)

                data = json.loads(file.read().decode("utf-8"))

                # Clear existing categories
                for category in category_set.categories:
                    db.session.delete(category)
                db.session.commit()

                # Insert new categories
                for item in data:
                    category = CustomEventCategory(
                        category_set_id=category_set_id, name=item
                    )
                    db.session.add(category)
                db.session.commit()

                flash(f"{len(data)} categories inserted successfully!", "success")
                return redirect(request.url)
            except Exception as e:
                db.session.rollback()
                flash(f"Error: {str(e)}", "error")
                return redirect(request.url)

        return self.render(
            "flask-admin/custom_category_extension_bulk_insert_view.html"
        )


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

    name = class_.get_display_name_plural()
    category = class_.get_display_name().split(" ")[0]

    admin.add_view(
        AuthModelView(
            class_,
            db.session,
            name=name,
            category=category,
        )
    )

admin.add_view(
    OrganizationView(
        AdminUnit,
        db.session,
        name="AdminUnit",
        category="Custom Views",
    )
)

admin.add_view(
    UserView(
        User,
        db.session,
        name="User",
        category="Custom Views",
    )
)

admin.add_view(
    EventPlaceView(
        EventPlace,
        db.session,
        name="EventPlace",
        category="Custom Views",
    )
)

admin.add_view(
    CustomCategoryExtensionView(
        name="Custom category extension", endpoint="custom_category_extension"
    )
)
