import type { EventInput } from "@fullcalendar/vue3";
import type { components } from "@/api/schema";

export type ManageEventDate = components["schemas"]["ManageEventDate"];

/** The badge variants of the event list and the date modal. */
export const publicStatusVariant: Record<string, string> = {
  draft: "light",
  published: "success",
  planned: "secondary",
};

export function statusVariant(name: string): string {
  return name === "scheduled" ? "success" : name === "cancelled" ? "danger" : "warning";
}

export function statusLabel(list: { name: string; label: string }[] | undefined, name: string) {
  return list?.find((s) => s.name === name)?.label ?? name;
}

/** The calendar colors per public status (FullCalendar 7 option names); published
 * matches the planning calendar. */
export const PUBLIC_STATUS_COLORS: Record<string, { color: string; contrastColor?: string }> = {
  published: { color: "#007bff" },
  planned: { color: "#6c757d" },
  draft: { color: "#adb5bd", contrastColor: "#212529" },
};

/** The CSS class of a date whose event is not scheduled as planned. */
function statusClass(status: string | null | undefined): string {
  if (!status || status === "scheduled") return "";
  return status === "cancelled" ? "ec-cancelled" : "ec-status-info";
}

export function toManageCalendarEvent(row: ManageEventDate): EventInput {
  const colors = PUBLIC_STATUS_COLORS[row.event.public_status] ?? PUBLIC_STATUS_COLORS.published;
  return {
    id: `d${row.id}`,
    title: row.event.name,
    start: row.start,
    end: row.end ?? undefined,
    allDay: row.allday,
    ...colors,
    className: statusClass(row.event.status),
    extendedProps: { row },
  };
}
