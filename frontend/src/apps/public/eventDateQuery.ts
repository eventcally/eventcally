import type { LocationQuery, LocationQueryRaw } from "vue-router";

/** The filter state of the event dates page; the URL keeps the names of the legacy form. */
export interface EventDateFilter {
  date_from: string;
  date_to: string;
  keyword: string;
  category_id: number | null;
  tag: string;
  admin_unit_id: number | null;
  organizer_id: number | null;
  postal_code: string;
  coordinate: string;
  /** The place label next to the coordinate; UI only. */
  location: string;
  distance: number | null;
  created_at_from: string;
  created_at_to: string;
  sort: "start" | "-created_at";
  exclude_recurring: boolean;
  not_referenced: boolean;
  page: number;
}

export interface EventDateDefaults {
  date_from: string;
}

const COORDINATE = /^-?\d+(\.\d+)?,-?\d+(\.\d+)?$/;
const DATE = /^\d{4}-\d{2}-\d{2}$/;

export function emptyFilter(defaults: EventDateDefaults): EventDateFilter {
  return {
    date_from: defaults.date_from,
    date_to: "",
    keyword: "",
    category_id: null,
    tag: "",
    admin_unit_id: null,
    organizer_id: null,
    postal_code: "",
    coordinate: "",
    location: "",
    distance: null,
    created_at_from: "",
    created_at_to: "",
    sort: "start",
    exclude_recurring: false,
    not_referenced: false,
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

function flag(value: LocationQuery[string]): boolean {
  return ["1", "true", "y", "on"].includes(text(value).toLowerCase());
}

/** Reads a (possibly legacy) URL; unusable values fall back to the defaults. */
export function fromRouteQuery(query: LocationQuery, defaults: EventDateDefaults): EventDateFilter {
  const filter = emptyFilter(defaults);
  const coordinate = text(query.coordinate);
  const hasCoordinate = COORDINATE.test(coordinate);

  filter.date_from = date(query.date_from) || defaults.date_from;
  filter.date_to = date(query.date_to);
  filter.keyword = text(query.keyword);
  // The legacy form sent `0` for "any category".
  filter.category_id = positiveInt(query.category_id);
  filter.tag = text(query.tag);
  filter.admin_unit_id = positiveInt(query.admin_unit_id);
  filter.organizer_id = positiveInt(query.organizer_id);
  filter.postal_code = text(query.postal_code);
  filter.coordinate = hasCoordinate ? coordinate : "";
  filter.location = hasCoordinate ? text(query.location) : "";
  // A radius needs a center.
  filter.distance = hasCoordinate ? positiveInt(query.distance) : null;
  filter.created_at_from = date(query.created_at_from);
  filter.created_at_to = date(query.created_at_to);
  filter.sort = text(query.sort) === "-created_at" ? "-created_at" : "start";
  filter.exclude_recurring = flag(query.exclude_recurring);
  filter.not_referenced = flag(query.not_referenced);
  filter.page = positiveInt(query.page) ?? 1;
  return filter;
}

/** The URL of a filter: defaults and empty values are left out. */
export function toRouteQuery(filter: EventDateFilter, defaults: EventDateDefaults): LocationQueryRaw {
  const query: Record<string, string> = {};
  const set = (key: string, value: string | number | null) => {
    if (value !== null && value !== "") query[key] = String(value);
  };

  if (filter.date_from !== defaults.date_from) set("date_from", filter.date_from);
  set("date_to", filter.date_to);
  set("keyword", filter.keyword.trim());
  set("category_id", filter.category_id);
  set("tag", filter.tag.trim());
  set("admin_unit_id", filter.admin_unit_id);
  set("organizer_id", filter.organizer_id);
  set("postal_code", filter.postal_code.trim());
  if (filter.coordinate) {
    set("coordinate", filter.coordinate);
    set("location", filter.location);
    set("distance", filter.distance);
  }
  set("created_at_from", filter.created_at_from);
  set("created_at_to", filter.created_at_to);
  if (filter.sort !== "start") set("sort", filter.sort);
  if (filter.exclude_recurring) query.exclude_recurring = "1";
  if (filter.not_referenced) query.not_referenced = "1";
  if (filter.page > 1) set("page", filter.page);
  return query;
}

/** The query of `GET /bff/public/event-dates`. */
export function toBffParams(filter: EventDateFilter) {
  return {
    page: filter.page,
    date_from: filter.date_from || undefined,
    date_to: filter.date_to || undefined,
    keyword: filter.keyword.trim() || undefined,
    category_id: filter.category_id ? [filter.category_id] : undefined,
    tag: filter.tag.trim() || undefined,
    admin_unit_id: filter.admin_unit_id ?? undefined,
    organizer_id: filter.organizer_id ?? undefined,
    postal_code: filter.postal_code.trim() || undefined,
    coordinate: filter.coordinate || undefined,
    distance: filter.coordinate ? (filter.distance ?? undefined) : undefined,
    created_at_from: filter.created_at_from || undefined,
    created_at_to: filter.created_at_to || undefined,
    sort: filter.sort,
    exclude_recurring: filter.exclude_recurring || undefined,
    not_referenced: filter.not_referenced || undefined,
  };
}

/** Whether a filter outside the always visible row is set (the "more filters" start expanded). */
export function hasExtendedFilter(filter: EventDateFilter): boolean {
  return Boolean(
    filter.category_id ||
      filter.tag ||
      filter.admin_unit_id ||
      filter.organizer_id ||
      filter.postal_code ||
      filter.coordinate ||
      filter.created_at_from ||
      filter.created_at_to ||
      filter.sort !== "start" ||
      filter.exclude_recurring ||
      filter.not_referenced,
  );
}
