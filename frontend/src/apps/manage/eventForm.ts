import type { components } from "@/api/schema";
import type { ImageValue } from "@/shared/ImageField.vue";

type Schemas = components["schemas"];
type EventForm = Schemas["EventForm"];
type DateDefinition = Schemas["EventDateDefinition"];

export interface Ref {
  id: number;
  name: string;
}

// One date of the form, as the date and time inputs hold it (Berlin wall clock).
export interface DateDefinitionValue {
  startDate: string;
  startTime: string;
  // The end is collapsed until "+ End" (the legacy `is_collapsible`).
  endShown: boolean;
  endDate: string;
  endTime: string;
  allday: boolean;
  recurrenceRule: string | null;
}

export interface EventFormValue {
  name: string;
  description: string;
  dateDefinitions: DateDefinitionValue[];
  status: Schemas["EventStatus"] | null;
  publicStatus: Schemas["EventPublicStatus"];
  organizer: Ref | null;
  eventPlace: Ref | null;
  coOrganizers: Ref[];
  categories: Ref[];
  // Selected custom categories by set id.
  customCategories: Record<number, Ref[]>;
  photo: ImageValue | null;
  externalLink: string;
  ticketLink: string;
  tags: string[];
  internalTags: string[];
  kidFriendly: boolean;
  accessibleForFree: boolean;
  registrationRequired: boolean;
  bookedUp: boolean;
  ageFrom: number | null;
  ageTo: number | null;
  expectedParticipants: number | null;
  priceInfo: string;
  targetGroupOrigin: Schemas["EventTargetGroupOrigin"];
  attendanceMode: Schemas["EventAttendanceMode"];
  rating: number;
  referenceRequestIds: number[];
}

// The 422 locations the page shows next to a field; `date_definitions.<i>.start|end` are
// added per date.
export const EVENT_FORM_FIELDS = [
  "name",
  "description",
  "date_definitions",
  "status",
  "public_status",
  "organizer_id",
  "event_place_id",
  "co_organizer_ids",
  "category_ids",
  "custom_category_ids",
  "photo.image_base64",
  "photo.copyright_text",
  "photo.license_id",
  "external_link",
  "ticket_link",
  "tags",
  "internal_tags",
  "age_from",
  "age_to",
  "expected_participants",
  "price_info",
  "target_group_origin",
  "attendance_mode",
  "rating",
  "reference_request_ids",
];

export function eventFormFields(dateCount: number): string[] {
  const dates = Array.from({ length: dateCount }, (_, i) => [
    `date_definitions.${i}.start`,
    `date_definitions.${i}.end`,
  ]).flat();
  return [...EVENT_FORM_FIELDS, ...dates];
}

function pad(value: number): string {
  return String(value).padStart(2, "0");
}

/** `YYYY-MM-DD` and `HH:MM` of a local date. */
export function splitDate(date: Date): { date: string; time: string } {
  return {
    date: `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`,
    time: `${pad(date.getHours())}:${pad(date.getMinutes())}`,
  };
}

/** The wall-clock `YYYY-MM-DDTHH:MM[:SS]` the server sends, as date and time. */
function splitWallClock(value: string): { date: string; time: string } {
  return { date: value.slice(0, 10), time: value.slice(11, 16) };
}

/**
 * The default end when "+ End" opens it: three hours after the start, or the end of the
 * start day for an all-day date (legacy `site.js`).
 */
export function defaultEnd(definition: DateDefinitionValue): { date: string; time: string } {
  if (definition.allday) return { date: definition.startDate, time: "23:59" };
  const [year, month, day] = definition.startDate.split("-").map(Number);
  const [hour, minute] = (definition.startTime || "00:00").split(":").map(Number);
  return splitDate(new Date(year, month - 1, day, hour + 3, minute));
}

export function newDateDefinition(start: { date: string; time: string }): DateDefinitionValue {
  return {
    startDate: start.date,
    startTime: start.time,
    endShown: false,
    endDate: "",
    endTime: "",
    allday: false,
    recurrenceRule: null,
  };
}

function dateDefinitionValue(definition: DateDefinition): DateDefinitionValue {
  const start = splitWallClock(definition.start);
  const end = definition.end ? splitWallClock(definition.end) : null;
  return {
    startDate: start.date,
    startTime: start.time,
    endShown: Boolean(end),
    endDate: end?.date ?? "",
    endTime: end?.time ?? "",
    allday: definition.allday ?? false,
    recurrenceRule: definition.recurrence_rule ?? null,
  };
}

function splitTags(value: string | null | undefined): string[] {
  return (value ?? "")
    .split(",")
    .map((tag) => tag.trim())
    .filter(Boolean);
}

export function eventFormValue(data: EventForm): EventFormValue {
  const choices = new Map(data.category_choices.map((choice) => [choice.id, choice]));
  return {
    name: data.name ?? "",
    description: data.description ?? "",
    dateDefinitions: data.date_definitions.map(dateDefinitionValue),
    // The server sends the enum values it offers as choices.
    status: (data.status ?? null) as Schemas["EventStatus"] | null,
    publicStatus: (data.public_status ?? 2) as Schemas["EventPublicStatus"],
    organizer: data.organizer ?? null,
    eventPlace: data.event_place ?? null,
    coOrganizers: data.co_organizers ?? [],
    categories: (data.category_ids ?? []).flatMap((id) => choices.get(id) ?? []),
    customCategories: Object.fromEntries(
      (data.custom_category_sets ?? []).map((set) => [set.id, set.selected ?? []]),
    ),
    // A template's photo is sent back as a new image; a stored one stays on the server.
    photo: data.photo
      ? {
          image_base64: data.id ? null : data.photo.image_base64 ?? null,
          copyright_text: data.photo.copyright_text ?? null,
          license_id: data.photo.license_id ?? null,
        }
      : null,
    externalLink: data.external_link ?? "",
    ticketLink: data.ticket_link ?? "",
    tags: splitTags(data.tags),
    internalTags: splitTags(data.internal_tags),
    kidFriendly: data.kid_friendly ?? false,
    accessibleForFree: data.accessible_for_free ?? false,
    registrationRequired: data.registration_required ?? false,
    bookedUp: data.booked_up ?? false,
    ageFrom: data.age_from ?? null,
    ageTo: data.age_to ?? null,
    expectedParticipants: data.expected_participants ?? null,
    priceInfo: data.price_info ?? "",
    targetGroupOrigin: data.target_group_origin as Schemas["EventTargetGroupOrigin"],
    attendanceMode: data.attendance_mode as Schemas["EventAttendanceMode"],
    rating: data.rating ?? 50,
    referenceRequestIds: data.reference_request_ids ?? [],
  };
}

function dateDefinitionBody(definition: DateDefinitionValue): DateDefinition {
  const startTime = definition.allday ? "00:00" : definition.startTime || "00:00";
  const endTime = definition.allday ? "23:59" : definition.endTime || "00:00";
  return {
    start: `${definition.startDate}T${startTime}`,
    end: definition.endShown && definition.endDate ? `${definition.endDate}T${endTime}` : null,
    allday: definition.allday,
    recurrence_rule: definition.recurrenceRule || null,
  };
}

function ids(refs: Ref[]): number[] {
  return refs.map((ref) => ref.id);
}

/** The fields create and update share. */
export function eventSaveBody(value: EventFormValue) {
  return {
    name: value.name,
    description: value.description,
    date_definitions: value.dateDefinitions.map(dateDefinitionBody),
    organizer_id: value.organizer?.id ?? null,
    event_place_id: value.eventPlace?.id ?? null,
    co_organizer_ids: ids(value.coOrganizers),
    category_ids: ids(value.categories),
    custom_category_ids: Object.values(value.customCategories).flatMap(ids),
    photo: value.photo ? { ...value.photo } : null,
    external_link: value.externalLink,
    ticket_link: value.ticketLink,
    tags: value.tags.join(","),
    internal_tags: value.internalTags.join(","),
    kid_friendly: value.kidFriendly,
    accessible_for_free: value.accessibleForFree,
    registration_required: value.registrationRequired,
    booked_up: value.bookedUp,
    age_from: value.ageFrom,
    age_to: value.ageTo,
    expected_participants: value.expectedParticipants,
    price_info: value.priceInfo,
    target_group_origin: value.targetGroupOrigin,
    attendance_mode: value.attendanceMode,
    rating: value.rating,
  };
}
