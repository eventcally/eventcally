import type { LocationQuery, LocationQueryRaw } from "vue-router";

export type ManageEventSort = "min_start" | "-last_modified_at" | "-created_at";

/** The filter state of the manage event list; the URL keeps the names of the legacy form. */
export interface ManageEventFilter {
  keyword: string;
  date_from: string;
  date_to: string;
  category_id: number | null;
  tag: string;
  internal_tag: string;
  organizer_id: number | null;
  event_place_id: number | null;
  postal_code: string;
  radius_coordinate: string;
  /** The place label next to the coordinate; UI only. */
  radius_location_name: string;
  radius_distance: number | null;
  status: number | null;
  public_status: number | null;
  created_at_from: string;
  created_at_to: string;
  /** "" (any), "1" (recurring) or "0" (not recurring). */
  is_recurring: "" | "1" | "0";
  sort: ManageEventSort;
  page: number;
}

export interface ManageEventDefaults {
  date_from: string;
}

const COORDINATE = /^-?\d+(\.\d+)?,-?\d+(\.\d+)?$/;
const DATE = /^\d{4}-\d{2}-\d{2}$/;
const SORTS: ManageEventSort[] = ["min_start", "-last_modified_at", "-created_at"];

export function emptyFilter(defaults: ManageEventDefaults): ManageEventFilter {
  return {
    keyword: "",
    date_from: defaults.date_from,
    date_to: "",
    category_id: null,
    tag: "",
    internal_tag: "",
    organizer_id: null,
    event_place_id: null,
    postal_code: "",
    radius_coordinate: "",
    radius_location_name: "",
    radius_distance: null,
    status: null,
    public_status: null,
    created_at_from: "",
    created_at_to: "",
    is_recurring: "",
    sort: "min_start",
    page: 1,
  };
}

function text(value: LocationQuery[string]): string {
  const first = Array.isArray(value) ? value[0] : value;
  return (first ?? "").trim();
}

function positiveInt(value: LocationQuery[string]): number | null {
  const parsed = Number.parseInt(text(value), 10);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : null;
}

function date(value: LocationQuery[string]): string {
  const raw = text(value);
  return DATE.test(raw) ? raw : "";
}

/** Reads a (possibly legacy) URL; unusable values (the legacy "all" is `-1`) fall back to the defaults. */
export function fromRouteQuery(
  query: LocationQuery,
  defaults: ManageEventDefaults,
): ManageEventFilter {
  const filter = emptyFilter(defaults);
  const coordinate = text(query.radius_coordinate);
  const hasCoordinate = COORDINATE.test(coordinate);
  const recurring = text(query.is_recurring);
  const sort = text(query.sort) as ManageEventSort;

  filter.keyword = text(query.keyword);
  filter.date_from = date(query.date_from) || defaults.date_from;
  filter.date_to = date(query.date_to);
  filter.category_id = positiveInt(query.category_id);
  filter.tag = text(query.tag);
  filter.internal_tag = text(query.internal_tag);
  filter.organizer_id = positiveInt(query.organizer_id);
  filter.event_place_id = positiveInt(query.event_place_id);
  filter.postal_code = text(query.postal_code);
  filter.radius_coordinate = hasCoordinate ? coordinate : "";
  filter.radius_location_name = hasCoordinate ? text(query.radius_location_name) : "";
  // A radius needs a center.
  filter.radius_distance = hasCoordinate ? positiveInt(query.radius_distance) : null;
  filter.status = positiveInt(query.status);
  filter.public_status = positiveInt(query.public_status);
  filter.created_at_from = date(query.created_at_from);
  filter.created_at_to = date(query.created_at_to);
  filter.is_recurring = recurring === "1" || recurring === "0" ? recurring : "";
  filter.sort = SORTS.includes(sort) ? sort : "min_start";
  filter.page = positiveInt(query.page) ?? 1;
  return filter;
}

/** The URL of a filter: defaults and empty values are left out. */
export function toRouteQuery(
  filter: ManageEventFilter,
  defaults: ManageEventDefaults,
): LocationQueryRaw {
  const query: Record<string, string> = {};
  const set = (key: string, value: string | number | null) => {
    if (value !== null && value !== "") query[key] = String(value);
  };

  set("keyword", filter.keyword.trim());
  if (filter.date_from !== defaults.date_from) set("date_from", filter.date_from);
  set("date_to", filter.date_to);
  set("category_id", filter.category_id);
  set("tag", filter.tag.trim());
  set("internal_tag", filter.internal_tag.trim());
  set("organizer_id", filter.organizer_id);
  set("event_place_id", filter.event_place_id);
  set("postal_code", filter.postal_code.trim());
  if (filter.radius_coordinate) {
    set("radius_coordinate", filter.radius_coordinate);
    set("radius_location_name", filter.radius_location_name);
    set("radius_distance", filter.radius_distance);
  }
  set("status", filter.status);
  set("public_status", filter.public_status);
  set("created_at_from", filter.created_at_from);
  set("created_at_to", filter.created_at_to);
  set("is_recurring", filter.is_recurring);
  if (filter.sort !== "min_start") set("sort", filter.sort);
  if (filter.page > 1) set("page", filter.page);
  return query;
}

/** The query of `GET /bff/manage/organizations/{id}/events`. */
export function toBffParams(filter: ManageEventFilter) {
  const located = Boolean(filter.radius_coordinate && filter.radius_distance);
  return {
    page: filter.page,
    keyword: filter.keyword.trim() || undefined,
    date_from: filter.date_from || undefined,
    date_to: filter.date_to || undefined,
    category_id: filter.category_id ?? undefined,
    tag: filter.tag.trim() || undefined,
    internal_tag: filter.internal_tag.trim() || undefined,
    organizer_id: filter.organizer_id ?? undefined,
    event_place_id: filter.event_place_id ?? undefined,
    postal_code: filter.postal_code.trim() || undefined,
    radius_coordinate: located ? filter.radius_coordinate : undefined,
    radius_distance: located ? (filter.radius_distance ?? undefined) : undefined,
    status: filter.status ?? undefined,
    public_status: filter.public_status ?? undefined,
    created_at_from: filter.created_at_from || undefined,
    created_at_to: filter.created_at_to || undefined,
    is_recurring: filter.is_recurring || undefined,
    sort: filter.sort,
  };
}

/** Whether a filter outside the always visible row (keyword, date range, sort) is set. */
export function hasExtendedFilter(filter: ManageEventFilter): boolean {
  return Boolean(
    filter.category_id ||
      filter.tag ||
      filter.internal_tag ||
      filter.organizer_id ||
      filter.event_place_id ||
      filter.postal_code ||
      filter.radius_coordinate ||
      filter.status ||
      filter.public_status ||
      filter.created_at_from ||
      filter.created_at_to ||
      filter.is_recurring,
  );
}
