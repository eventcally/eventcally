import type { EventInput } from "@fullcalendar/vue3";
import type { components } from "@/api/schema";

export type PlanningEventDate = components["schemas"]["PlanningEventDate"];
export type ExternalCalendarEvent = components["schemas"]["ExternalCalendarEvent"];
export type PlanningExternalCalendar = components["schemas"]["PlanningExternalCalendar"];

export const COLORS = {
  default: "#007bff",
  statusInfo: "#17a2b8",
  external: "#aa7bff",
};

export type CalendarEventProps =
  | { kind: "date"; row: PlanningEventDate }
  | { kind: "external"; item: ExternalCalendarEvent; calendar: { title: string; url: string } };

export function toCalendarEvent(row: PlanningEventDate): EventInput {
  const props: CalendarEventProps = { kind: "date", row };
  return {
    id: `d${row.id}`,
    title: row.event.name,
    start: row.start,
    end: row.end ?? undefined,
    allDay: row.allday,
    color: row.event.has_status_info ? COLORS.statusInfo : COLORS.default,
    extendedProps: props,
  };
}

export function toExternalEvent(
  item: ExternalCalendarEvent,
  calendar: { title: string; url: string },
  index: number,
): EventInput {
  const props: CalendarEventProps = { kind: "external", item, calendar };
  return {
    id: `x${calendar.url}#${index}`,
    title: item.name,
    start: item.start,
    end: item.end ?? undefined,
    allDay: item.allday,
    color: COLORS.external,
    extendedProps: props,
  };
}

function localDate(d: Date): string {
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

/** The visible range as `YYYY-MM-DD` (local time); FullCalendar's `end` is exclusive. */
export function rangeFromDatesSet({ start, end }: { start: Date; end: Date }) {
  const last = new Date(end.getTime());
  last.setDate(last.getDate() - 1);
  return { date_from: localDate(start), date_to: localDate(last) };
}

/** The earliest start hour of the timed rows, or `null` when there are none. */
export function earliestHour(rows: PlanningEventDate[]): number | null {
  const hours = rows.filter((r) => !r.allday).map((r) => new Date(r.start).getHours());
  return hours.length ? Math.min(...hours) : null;
}

export interface PlanningFilter {
  category_id: number[];
  postal_code: string;
  coordinate: string;
  location_name: string;
  distance: number | null;
  expected_participants_min: number | null;
  exclude_recurring: boolean;
}

export function emptyFilter(): PlanningFilter {
  return {
    category_id: [],
    postal_code: "",
    coordinate: "",
    location_name: "",
    distance: null,
    expected_participants_min: null,
    exclude_recurring: true,
  };
}

/** The filter as event-dates query parameters; empty values are dropped. */
export function filterToQuery(filter: PlanningFilter) {
  const query: {
    category_id?: number[];
    postal_code?: string;
    coordinate?: string;
    distance?: number;
    expected_participants_min?: number;
    exclude_recurring: boolean;
  } = { exclude_recurring: filter.exclude_recurring };
  if (filter.category_id.length) query.category_id = filter.category_id;
  if (filter.postal_code.trim()) query.postal_code = filter.postal_code.trim();
  if (filter.coordinate) {
    query.coordinate = filter.coordinate;
    if (filter.distance !== null) query.distance = filter.distance;
  }
  if (filter.expected_participants_min !== null) {
    query.expected_participants_min = filter.expected_participants_min;
  }
  return query;
}
