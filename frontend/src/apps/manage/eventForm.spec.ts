import { describe, expect, it } from "vitest";
import type { components } from "@/api/schema";
import {
  defaultEnd,
  eventFormFields,
  eventFormValue,
  eventSaveBody,
  newDateDefinition,
  splitDate,
} from "./eventForm";

type EventForm = components["schemas"]["EventForm"];

function form(overrides: Partial<EventForm> = {}): EventForm {
  return {
    id: null,
    name: "",
    description: null,
    date_definitions: [
      { start: "2030-12-31T14:00:00", end: null, allday: false, recurrence_rule: null },
    ],
    status: null,
    public_status: 2,
    status_choices: [],
    public_status_choices: [],
    organizer: null,
    event_place: null,
    co_organizers: [],
    category_ids: [3],
    category_choices: [
      { id: 3, name: "Other" },
      { id: 4, name: "Music" },
    ],
    custom_category_sets: [{ id: 7, label: "Region", selected: [{ id: 8, name: "Harz" }] }],
    photo: null,
    licenses: [],
    external_link: null,
    ticket_link: null,
    tags: "a, b,",
    internal_tags: null,
    kid_friendly: false,
    accessible_for_free: false,
    registration_required: false,
    booked_up: false,
    age_from: null,
    age_to: null,
    expected_participants: null,
    price_info: null,
    target_group_origin: 1,
    target_group_origin_choices: [],
    attendance_mode: 1,
    attendance_mode_choices: [],
    rating: 50,
    rating_choices: [],
    reference_request_choices: [],
    reference_request_ids: [],
    can_create_place: true,
    can_create_organizer: true,
    ...overrides,
  };
}

describe("eventForm", () => {
  it("maps a create form to the field values", () => {
    const value = eventFormValue(form());

    expect(value.dateDefinitions).toEqual([
      {
        startDate: "2030-12-31",
        startTime: "14:00",
        endShown: false,
        endDate: "",
        endTime: "",
        allday: false,
        recurrenceRule: null,
      },
    ]);
    expect(value.categories).toEqual([{ id: 3, name: "Other" }]);
    expect(value.customCategories).toEqual({ 7: [{ id: 8, name: "Harz" }] });
    expect(value.tags).toEqual(["a", "b"]);
    expect(value.internalTags).toEqual([]);
    expect(value.status).toBeNull();
  });

  it("keeps a stored photo on the server but resends a template's photo", () => {
    const photo = { image_base64: "data:image/png;base64,x", copyright_text: "Me", license_id: 1 };

    expect(eventFormValue(form({ id: 5, photo })).photo).toEqual({ ...photo, image_base64: null });
    expect(eventFormValue(form({ photo })).photo).toEqual(photo);
  });

  it("reads an end and a recurrence", () => {
    const value = eventFormValue(
      form({
        date_definitions: [
          {
            start: "2030-12-31T00:00:00",
            end: "2031-01-01T23:59:00",
            allday: true,
            recurrence_rule: "RRULE:FREQ=DAILY",
          },
        ],
      }),
    );

    expect(value.dateDefinitions[0]).toMatchObject({
      endShown: true,
      endDate: "2031-01-01",
      endTime: "23:59",
      allday: true,
      recurrenceRule: "RRULE:FREQ=DAILY",
    });
  });

  it("builds the save body", () => {
    const value = eventFormValue(form());
    value.dateDefinitions.push({
      ...newDateDefinition({ date: "2031-01-02", time: "" }),
      allday: true,
      endShown: true,
      endDate: "2031-01-03",
      recurrenceRule: "",
    });
    value.dateDefinitions.push({
      ...newDateDefinition({ date: "2031-01-04", time: "10:00" }),
      endShown: true,
      endDate: "2031-01-04",
      endTime: "",
    });
    value.organizer = { id: 1, name: "Org" };
    value.coOrganizers = [{ id: 2, name: "Co" }];

    const body = eventSaveBody(value);

    expect(body.date_definitions).toEqual([
      { start: "2030-12-31T14:00", end: null, allday: false, recurrence_rule: null },
      { start: "2031-01-02T00:00", end: "2031-01-03T23:59", allday: true, recurrence_rule: null },
      { start: "2031-01-04T10:00", end: "2031-01-04T00:00", allday: false, recurrence_rule: null },
    ]);
    expect(body).toMatchObject({
      organizer_id: 1,
      event_place_id: null,
      co_organizer_ids: [2],
      category_ids: [3],
      custom_category_ids: [8],
      tags: "a,b",
      internal_tags: "",
      photo: null,
    });
  });

  it("defaults the end three hours after the start or to the end of the day", () => {
    const definition = newDateDefinition({ date: "2030-12-31", time: "22:30" });

    expect(defaultEnd(definition)).toEqual({ date: "2031-01-01", time: "01:30" });
    expect(defaultEnd({ ...definition, startTime: "" })).toEqual({ date: "2030-12-31", time: "03:00" });
    expect(defaultEnd({ ...definition, allday: true })).toEqual({ date: "2030-12-31", time: "23:59" });
  });

  it("lists the error locations of every date", () => {
    expect(eventFormFields(2)).toEqual(
      expect.arrayContaining([
        "name",
        "date_definitions.0.start",
        "date_definitions.1.end",
      ]),
    );
    expect(splitDate(new Date(2030, 0, 2, 3, 4))).toEqual({ date: "2030-01-02", time: "03:04" });
  });
});
