from typing import Annotated

from dependency_injector.wiring import Provide
from flask import flash, request, url_for
from flask_babel import gettext

from project.access import can_request_event_reference_from_admin_unit
from project.dateutils import get_next_full_hour, get_today
from project.models.event import Event, PublicStatus
from project.models.event_reference_request import EventReferenceRequest
from project.modular.base_views import (
    BaseCreateView,
    BaseDeleteView,
    BaseListView,
    BaseUpdateView,
)
from project.services import organization_service
from project.services.admin_unit import (
    get_admin_unit_suggestions_for_reference_requests,
)
from project.services.event_category_service import EventCategoryService
from project.services.event_service import EventService
from project.views.manage_admin_unit.event.forms import CreateForm, UpdateForm
from project.views.reference_request import get_success_text_for_request_creation
from project.views.utils import current_admin_unit, flash_message


def prepare_date_definition(form):
    next_full_hour = get_next_full_hour()
    form.date_definition_template.start.data = next_full_hour

    if not form.date_definitions[0].start.data:
        form.date_definitions[0].start.data = next_full_hour


def prepare_event_form(form):
    prepare_date_definition(form)


def prepare_form_reference_requests(form, admin_unit):
    if not can_request_event_reference_from_admin_unit(admin_unit):
        form.reference_request_admin_unit_id.choices = []
        return

    (
        admin_unit_choices,
        selected_ids,
    ) = get_admin_unit_suggestions_for_reference_requests(admin_unit)

    form.reference_request_admin_unit_id.choices = sorted(
        [(a.id, a.name) for a in admin_unit_choices],
        key=lambda a: a[1],
    )

    if not form.is_submitted():
        form.reference_request_admin_unit_id.data = selected_ids


class CreateView(BaseCreateView):
    form_class = CreateForm
    event_service: Annotated[EventService, Provide["services.event_service"]]
    organization_service: Annotated[
        organization_service.OrganizationService,
        Provide["services.organization_service"],
    ]
    event_category_service: Annotated[
        EventCategoryService,
        Provide["services.event_category_service"],
    ]

    def create_form(self, **kwargs):
        kwargs.setdefault(
            "categories", [self.event_category_service.upsert_event_category("Other")]
        )
        form = super().create_form(**kwargs)
        prepare_event_form(form)
        prepare_form_reference_requests(form, current_admin_unit)

        # Vorlagen
        if not form.is_submitted():
            event_template_id = (
                int(request.args.get("template_id"))
                if "template_id" in request.args
                else 0
            )
            if event_template_id > 0:
                event_template = Event.query.get_or_404(event_template_id)
                form.process(obj=event_template)

        return form

    def complete_object(self, object, form):
        super().complete_object(object, form)

        if form.event_place_choice.data == 2:
            object.event_place.admin_unit_id = object.admin_unit_id

        if form.organizer_choice.data == 2:
            object.organizer.admin_unit_id = object.admin_unit_id

    def insert_object(self, object, form):
        self.event_service.insert_object(object)

        if (
            object.public_status == PublicStatus.published
            and form.reference_request_admin_unit_id.data
        ):
            for target_admin_unit_id in form.reference_request_admin_unit_id.data:
                reference_request = EventReferenceRequest()
                reference_request.event_id = object.id
                reference_request.admin_unit_id = target_admin_unit_id

                self.organization_service.insert_outgoing_event_reference_request(
                    reference_request
                )
                msg = get_success_text_for_request_creation(reference_request)
                flash(msg, "success")

    def flash_success_message(self, object, form):
        success_msg = (
            gettext("Event successfully published")
            if object.public_status == PublicStatus.published
            else (
                gettext("Draft successfully saved")
                if object.public_status == PublicStatus.draft
                else gettext("Event successfully planned")
            )
        )
        flash_message(
            success_msg,
            url_for("event", event_id=object.id),
        )

    def get_redirect_url(self, object, **kwargs):
        return url_for("event_actions", event_id=object.id)


class UpdateView(BaseUpdateView):
    form_class = UpdateForm
    event_service: Annotated[EventService, Provide["services.event_service"]]

    def create_form(self, **kwargs):
        form = super().create_form(**kwargs)
        prepare_event_form(form)
        return form

    def save_object(self, object, form):
        self.event_service.update_object(object)


class DeleteView(BaseDeleteView):
    pass


class ListView(BaseListView):
    def create_form(self, **kwargs):
        form = super().create_form(**kwargs)

        if not form.is_submitted() and not form.date.form.from_field.data:
            form.date.form.from_field.data = get_today()

        return form
