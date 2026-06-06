from dateutil.relativedelta import relativedelta
from flask_babel import gettext, lazy_gettext
from wtforms import (
    BooleanField,
    FormField,
    IntegerField,
    RadioField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.fields import FieldList, URLField
from wtforms.validators import DataRequired, Length, Optional

from project.application.commands.create_event_command import CreateEventCommand
from project.application.commands.create_event_organizer_command import (
    CreateEventOrganizerCommand,
)
from project.application.commands.create_event_place_command import (
    CreateEventPlaceCommand,
)
from project.application.commands.update_event_command import UpdateEventCommand
from project.domain.models.value_objects.event_date_definition_value_object import (
    EventDateDefinitionValueObject,
)
from project.forms.common import Base64ImageForm, LocationForm, event_rating_choices
from project.forms.widgets import (
    CustomDateTimeField,
    HTML5StringField,
    MultiCheckboxField,
)
from project.models import (
    EventAttendanceMode,
    EventDateDefinition,
    EventPublicStatus,
    EventStatus,
    EventTargetGroupOrigin,
    Image,
)
from project.models.event_organizer import EventOrganizer
from project.models.event_place import EventPlace
from project.models.location import Location
from project.modular.ajax import CustomEventCategoryLoader, EventCategoryAjaxModelLoader
from project.modular.base_form import BaseCreateForm, BaseForm, BaseUpdateForm
from project.modular.fields import AjaxSelectField, AjaxSelectMultipleField
from project.views.manage_admin_unit.ajax import (
    EventOrganizerAjaxModelLoader,
    EventPlaceAjaxModelLoader,
)


class EventDateDefinitionFormMixin:
    start = CustomDateTimeField(
        lazy_gettext("Start"),
        validators=[DataRequired()],
        description=lazy_gettext("Indicate when the event date will start."),
    )
    end = CustomDateTimeField(
        lazy_gettext("End"),
        validators=[Optional()],
        description=lazy_gettext(
            "Indicate when the event date will end. An event can last a maximum of 180 days."
        ),
    )
    allday = BooleanField(
        lazy_gettext("All-day"),
        validators=[Optional()],
    )
    recurrence_rule = TextAreaField(
        lazy_gettext("Recurring event"),
        validators=[Optional()],
    )

    def validate_date_definition(self):
        if self.start.data and self.end.data:
            if self.start.data > self.end.data:
                msg = gettext("The start must be before the end.")
                self.start.errors.append(msg)
                return False

            max_end = self.start.data + relativedelta(days=180)
            if self.end.data > max_end:
                msg = gettext("An event can last a maximum of 180 days.")
                self.end.errors.append(msg)
                return False
        return True


class EventDateDefinitionForm(BaseForm, EventDateDefinitionFormMixin):
    class Meta:
        csrf = False

    def validate(self, extra_validators=None):
        result = super().validate(extra_validators)

        if not self.validate_date_definition():
            result = False

        return result

    def create_value_object(self):
        return EventDateDefinitionValueObject(
            start=self.start.data,
            end=self.end.data,
            allday=self.allday.data,
            recurrence_rule=self.recurrence_rule.data,
        )


class CustomEventCategoryForm(BaseForm):
    def __init__(self, *args, **kwargs):
        from project.models.event_category import CustomEventCategorySet

        for category_set in CustomEventCategorySet.query.all():
            field_name = f"set_{category_set.id}"
            field = AjaxSelectMultipleField(
                CustomEventCategoryLoader(category_set_id=category_set.id),
                label=category_set.label_or_name,
                validators=[Optional()],
            )
            self._unbound_fields.append((field_name, field))

        super().__init__(*args, **kwargs)

    def process(self, formdata=None, obj=None, data=None, extra_filters=None, **kwargs):
        from project.models.event_category import CustomEventCategorySet

        if obj:
            categories = obj
            for category_set in CustomEventCategorySet.query.all():
                field_name = f"set_{category_set.id}"
                field_data = list(
                    filter(lambda c: c.category_set_id == category_set.id, categories)
                )
                kwargs.setdefault(field_name, field_data)

        return super().process(formdata, obj, data, extra_filters, **kwargs)

    def get_category_ids(self):
        category_ids = []
        for name, field in self._fields.items():
            if (
                name.startswith("set_")
                and field.data
                and isinstance(field, AjaxSelectMultipleField)
            ):
                data_ids = field.get_data_ids()
                if data_ids:
                    category_ids.extend(data_ids)
        return category_ids


class EventFormMixin(object):
    name = HTML5StringField(
        lazy_gettext("Name"),
        validators=[DataRequired(), Length(min=3, max=255)],
        description=lazy_gettext("Enter a short, meaningful name for the event."),
    )
    description = TextAreaField(
        lazy_gettext("Description"),
        validators=[Optional()],
        description=lazy_gettext("Add an description of the event."),
    )
    external_link = URLField(
        lazy_gettext("Link URL"),
        validators=[Optional(), Length(max=255)],
        description=lazy_gettext(
            "Enter a link to an external website containing more information about the event."
        ),
    )
    ticket_link = URLField(
        lazy_gettext("Ticket Link URL"),
        validators=[Optional(), Length(max=255)],
        description=lazy_gettext("Enter a link where tickets can be purchased."),
    )
    tags = StringField(
        lazy_gettext("Tags"),
        validators=[Optional()],
        description=lazy_gettext(
            "Enter keywords with which the event should be found. Words do not need to be entered if they are already in the name or description."
        ),
    )
    internal_tags = StringField(
        lazy_gettext("Internal tags"),
        validators=[Optional()],
        description=lazy_gettext(
            "Keywords for internal use. These will not be published."
        ),
    )
    kid_friendly = BooleanField(
        lazy_gettext("Kid friendly"),
        validators=[Optional()],
        description=lazy_gettext("If the event is particularly suitable for children."),
    )
    accessible_for_free = BooleanField(
        lazy_gettext("Accessible for free"),
        validators=[Optional()],
        description=lazy_gettext("If the event is accessible for free."),
    )
    age_from = IntegerField(
        lazy_gettext("Typical Age from"),
        validators=[Optional()],
        description=lazy_gettext("The minimum age that participants should be."),
    )
    age_to = IntegerField(
        lazy_gettext("Typical Age to"),
        validators=[Optional()],
        description=lazy_gettext("The maximum age that participants should be."),
    )
    registration_required = BooleanField(
        lazy_gettext("Registration required"),
        validators=[Optional()],
        description=lazy_gettext(
            "If the participants needs to register for the event."
        ),
    )
    booked_up = BooleanField(
        lazy_gettext("Booked up"),
        validators=[Optional()],
        description=lazy_gettext("If the event is booked up or sold out."),
    )
    expected_participants = IntegerField(
        lazy_gettext("Expected number of participants"),
        validators=[Optional()],
        description=lazy_gettext("The estimated expected attendance."),
    )
    price_info = TextAreaField(
        lazy_gettext("Price info"),
        validators=[Optional()],
        description=lazy_gettext(
            "Enter price information in textual form. E.g., different prices for adults and children."
        ),
    )
    target_group_origin = SelectField(
        lazy_gettext("Target group origin"),
        coerce=int,
        choices=[
            (
                int(EventTargetGroupOrigin.both),
                lazy_gettext("EventTargetGroupOrigin.both"),
            ),
            (
                int(EventTargetGroupOrigin.tourist),
                lazy_gettext("EventTargetGroupOrigin.tourist"),
            ),
            (
                int(EventTargetGroupOrigin.resident),
                lazy_gettext("EventTargetGroupOrigin.resident"),
            ),
        ],
        description=lazy_gettext(
            "Choose whether the event is particularly suitable for tourists or residents."
        ),
    )
    attendance_mode = SelectField(
        lazy_gettext("Attendance mode"),
        coerce=int,
        choices=[
            (
                int(EventAttendanceMode.offline),
                lazy_gettext("EventAttendanceMode.offline"),
            ),
            (
                int(EventAttendanceMode.online),
                lazy_gettext("EventAttendanceMode.online"),
            ),
            (int(EventAttendanceMode.mixed), lazy_gettext("EventAttendanceMode.mixed")),
        ],
        description=lazy_gettext("Choose how people can attend the event."),
    )
    photo = FormField(
        Base64ImageForm,
        lazy_gettext("Photo"),
        default=lambda: Image(),
        description=lazy_gettext(
            "We recommend uploading a photo for the event. It looks a lot more, but of course it works without it."
        ),
    )
    date_definitions = FieldList(
        FormField(EventDateDefinitionForm, default=lambda: EventDateDefinition()),
        min_entries=1,
    )
    date_definition_template = FormField(
        EventDateDefinitionForm, default=lambda: EventDateDefinition()
    )
    previous_start_date = CustomDateTimeField(
        lazy_gettext("Previous start date"),
        validators=[Optional()],
        description=lazy_gettext(
            "Enter when the event should have taken place before it was postponed."
        ),
    )
    categories = AjaxSelectMultipleField(
        EventCategoryAjaxModelLoader(),
        lazy_gettext("Categories"),
        validators=[DataRequired()],
        description=lazy_gettext("Choose categories that fit the event."),
    )
    custom_categories = FormField(
        CustomEventCategoryForm,
        lazy_gettext("Custom event categories"),
    )
    rating = SelectField(
        lazy_gettext("Rating"),
        default=50,
        coerce=int,
        choices=event_rating_choices,
        description=lazy_gettext(
            "Choose how relevant the event is to your organization. The value is not visible and is used for sorting."
        ),
    )
    co_organizers = AjaxSelectMultipleField(
        EventOrganizerAjaxModelLoader(),
        lazy_gettext("Co-organizers"),
        validators=[Optional()],
        description=lazy_gettext(
            "Select optional co-organizers. You can add and modify organizers at Organization > Organizers."
        ),
    )


class EventPlaceForm(BaseForm):
    name = StringField(
        lazy_gettext("Name"),
        validators=[Optional()],
    )
    location = FormField(LocationForm, default=lambda: Location())

    def create_create_command(self, admin_unit_id: int) -> CreateEventPlaceCommand:
        return CreateEventPlaceCommand.model_construct(
            admin_unit_id=admin_unit_id,
            name=self.name.data,
            location=self.location.form.create_create_command(),
        )


class OrganizerForm(BaseForm):
    name = StringField(
        lazy_gettext("Name"),
        validators=[Optional()],
    )
    location = FormField(LocationForm, default=lambda: Location())

    def create_create_command(self, admin_unit_id: int) -> CreateEventOrganizerCommand:
        return CreateEventOrganizerCommand.model_construct(
            admin_unit_id=admin_unit_id,
            name=self.name.data,
            location=self.location.form.create_create_command(),
        )


class CreateForm(BaseCreateForm, EventFormMixin):
    event_place_choice = RadioField(
        lazy_gettext("Place"),
        choices=[
            (1, lazy_gettext("Select existing place")),
            (2, lazy_gettext("Enter new place")),
        ],
        default=1,
        coerce=int,
    )
    event_place = AjaxSelectField(
        EventPlaceAjaxModelLoader(),
        lazy_gettext("Place"),
        validators=[Optional()],
        allow_blank=True,
    )
    new_event_place = FormField(EventPlaceForm, default=lambda: EventPlace())

    organizer_choice = RadioField(
        lazy_gettext("Organizer"),
        choices=[
            (1, lazy_gettext("Select existing organizer")),
            (2, lazy_gettext("Enter new organizer")),
        ],
        default=1,
        coerce=int,
    )
    organizer = AjaxSelectField(
        EventOrganizerAjaxModelLoader(),
        lazy_gettext("Organizer"),
        validators=[Optional()],
        allow_blank=True,
    )
    new_organizer = FormField(OrganizerForm, default=lambda: EventOrganizer())

    reference_request_admin_unit_id = MultiCheckboxField(
        lazy_gettext("Reference requests"), validators=[Optional()], coerce=int
    )

    submit_draft = SubmitField(lazy_gettext("Save as draft"))
    submit_planned = SubmitField(lazy_gettext("Save as planned"))
    submit = SubmitField(lazy_gettext("Publish event"))

    def create_create_command(
        self, admin_unit_id: int, event_place_id: int, organizer_id: int
    ) -> CreateEventCommand:
        date_definitions = [
            dd_form.create_value_object() for dd_form in self.date_definitions.entries
        ]
        category_ids = self.categories.get_data_ids()
        co_organizer_ids = self.co_organizers.get_data_ids()
        custom_category_ids = self.custom_categories.get_category_ids()

        public_status = (
            EventPublicStatus.published
            if self.submit.data
            else (
                EventPublicStatus.planned
                if self.submit_planned.data
                else EventPublicStatus.draft
            )
        )
        return CreateEventCommand.model_construct(
            admin_unit_id=admin_unit_id,
            name=self.name.data,
            organizer_id=organizer_id,
            event_place_id=event_place_id,
            date_definitions=date_definitions,
            status=EventStatus.scheduled,
            public_status=public_status,
            description=self.description.data,
            external_link=self.external_link.data,
            ticket_link=self.ticket_link.data,
            tags=self.tags.data,
            internal_tags=self.internal_tags.data,
            kid_friendly=self.kid_friendly.data,
            accessible_for_free=self.accessible_for_free.data,
            age_from=self.age_from.data,
            age_to=self.age_to.data,
            registration_required=self.registration_required.data,
            booked_up=self.booked_up.data,
            expected_participants=self.expected_participants.data,
            price_info=self.price_info.data,
            target_group_origin=self.target_group_origin.data,
            attendance_mode=self.attendance_mode.data,
            photo=self.photo.form.create_create_command(),
            previous_start_date=self.previous_start_date.data,
            category_ids=category_ids,
            custom_category_ids=custom_category_ids,
            rating=self.rating.data,
            co_organizer_ids=co_organizer_ids,
        )

    def validate(self, extra_validators=None):
        result = super().validate(extra_validators)

        if not self.event_place.data and not self.new_event_place.form.name.data:
            msg = gettext("Select existing place or enter new place")
            self.event_place.errors.append(msg)
            self.new_event_place.form.name.errors.append(msg)
            result = False

        if not self.organizer.data and not self.new_organizer.form.name.data:
            msg = gettext("Select existing organizer or enter new organizer")
            self.organizer.errors.append(msg)
            self.new_organizer.form.name.errors.append(msg)
            result = False

        return result


class UpdateForm(BaseUpdateForm, EventFormMixin):
    event_place = AjaxSelectField(
        EventPlaceAjaxModelLoader(),
        lazy_gettext("Place"),
        validators=[DataRequired()],
        description=lazy_gettext(
            "Choose where the event takes place. You can add and modify places at Organization > Places."
        ),
    )
    organizer = AjaxSelectField(
        EventOrganizerAjaxModelLoader(),
        lazy_gettext("Organizer"),
        validators=[DataRequired()],
        description=lazy_gettext(
            "Select the organizer. You can add and modify organizers at Organization > Organizers."
        ),
    )

    status = SelectField(
        lazy_gettext("Status"),
        coerce=int,
        choices=[
            (int(EventStatus.scheduled), lazy_gettext("EventStatus.scheduled")),
            (int(EventStatus.cancelled), lazy_gettext("EventStatus.cancelled")),
            (int(EventStatus.movedOnline), lazy_gettext("EventStatus.movedOnline")),
            (int(EventStatus.postponed), lazy_gettext("EventStatus.postponed")),
            (int(EventStatus.rescheduled), lazy_gettext("EventStatus.rescheduled")),
        ],
        description=lazy_gettext("Select the status of the event."),
    )

    public_status = SelectField(
        lazy_gettext("Public status"),
        coerce=int,
        choices=[
            (
                int(EventPublicStatus.published),
                lazy_gettext("EventPublicStatus.published"),
            ),
            (int(EventPublicStatus.planned), lazy_gettext("EventPublicStatus.planned")),
            (int(EventPublicStatus.draft), lazy_gettext("EventPublicStatus.draft")),
        ],
        description=lazy_gettext(
            "Planned events appear in the scheduling view, but not on public calendars."
        ),
    )

    def create_update_command(self, event_id: int) -> UpdateEventCommand:
        date_definitions = [
            dd_form.create_value_object() for dd_form in self.date_definitions.entries
        ]
        category_ids = self.categories.get_data_ids()
        co_organizer_ids = self.co_organizers.get_data_ids()
        custom_category_ids = self.custom_categories.get_category_ids()

        return UpdateEventCommand.model_construct(
            id=event_id,
            name=self.name.data,
            organizer_id=self.organizer.data.id,
            event_place_id=self.event_place.data.id,
            date_definitions=date_definitions,
            status=self.status.data,
            public_status=self.public_status.data,
            description=self.description.data,
            external_link=self.external_link.data,
            ticket_link=self.ticket_link.data,
            tags=self.tags.data,
            internal_tags=self.internal_tags.data,
            kid_friendly=self.kid_friendly.data,
            accessible_for_free=self.accessible_for_free.data,
            age_from=self.age_from.data,
            age_to=self.age_to.data,
            registration_required=self.registration_required.data,
            booked_up=self.booked_up.data,
            expected_participants=self.expected_participants.data,
            price_info=self.price_info.data,
            target_group_origin=self.target_group_origin.data,
            attendance_mode=self.attendance_mode.data,
            photo=self.photo.form.create_update_command(),
            previous_start_date=self.previous_start_date.data,
            category_ids=category_ids,
            custom_category_ids=custom_category_ids,
            rating=self.rating.data,
            co_organizer_ids=co_organizer_ids,
        )
