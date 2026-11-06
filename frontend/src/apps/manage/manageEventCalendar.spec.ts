import { describe, expect, it } from "vitest";
import {
  statusLabel,
  statusVariant,
  toManageCalendarEvent,
  type ManageEventDate,
} from "./manageEventCalendar";

const row = (event: Partial<ManageEventDate["event"]> = {}): ManageEventDate => ({
  id: 7,
  start: "2030-10-03T08:00:00Z",
  end: null,
  allday: false,
  event: {
    id: 11,
    name: "Jam Session",
    is_recurring: false,
    status: "scheduled",
    public_status: "published",
    organizer_name: null,
    place_label: null,
    ...event,
  },
});

describe("manageEventCalendar", () => {
  it("maps a published, scheduled date", () => {
    const input = row();
    expect(toManageCalendarEvent(input)).toEqual({
      id: "d7",
      title: "Jam Session",
      start: "2030-10-03T08:00:00Z",
      end: undefined,
      allDay: false,
      color: "#007bff",
      className: "",
      extendedProps: { row: input },
    });
  });

  it("colors drafts and planned dates and marks a status other than scheduled", () => {
    const draft = toManageCalendarEvent(row({ public_status: "draft", status: "cancelled" }));
    expect(draft.color).toBe("#adb5bd");
    expect(draft.contrastColor).toBe("#212529");
    expect(draft.className).toBe("ec-cancelled");

    const planned = toManageCalendarEvent({ ...row({ public_status: "planned", status: null }), end: "2030-10-03T10:00:00Z" });
    expect(planned.color).toBe("#6c757d");
    expect(planned.className).toBe("");
    expect(planned.end).toBe("2030-10-03T10:00:00Z");

    expect(toManageCalendarEvent(row({ public_status: "unknown" })).color).toBe("#007bff");
    expect(toManageCalendarEvent(row({ status: "postponed" })).className).toBe("ec-status-info");
  });

  it("picks badge variants and labels", () => {
    expect(statusVariant("scheduled")).toBe("success");
    expect(statusVariant("cancelled")).toBe("danger");
    expect(statusVariant("postponed")).toBe("warning");
    expect(statusLabel([{ name: "draft", label: "Entwurf" }], "draft")).toBe("Entwurf");
    expect(statusLabel(undefined, "draft")).toBe("draft");
  });
});
