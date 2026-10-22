import { describe, expect, it } from "vitest";
import {
  COLORS,
  earliestHour,
  emptyFilter,
  filterToQuery,
  rangeFromDatesSet,
  toCalendarEvent,
  toExternalEvent,
  type PlanningEventDate,
} from "./planning";

function row(over: Partial<PlanningEventDate> = {}, statusInfo = false): PlanningEventDate {
  return {
    id: 5,
    start: "2026-10-03T08:00:00Z",
    end: null,
    allday: false,
    event: {
      id: 1,
      name: "Jam",
      status: "scheduled",
      public_status: "published",
      booked_up: null,
      attendance_mode: "offline",
      has_status_info: statusInfo,
      organization_name: "Org",
      organizer_name: null,
      place_name: null,
    },
    ...over,
  };
}

describe("toCalendarEvent", () => {
  it("maps a row with the default colour", () => {
    expect(toCalendarEvent(row())).toMatchObject({
      id: "d5",
      title: "Jam",
      start: "2026-10-03T08:00:00Z",
      allDay: false,
      color: COLORS.default,
      extendedProps: { kind: "date" },
    });
  });

  it("colours rows with status info", () => {
    expect(toCalendarEvent(row({}, true)).color).toBe(COLORS.statusInfo);
  });
});

describe("toExternalEvent", () => {
  it("maps an item with the external colour", () => {
    const calendar = { title: "Holidays", url: "http://h" };
    const event = toExternalEvent(
      {
        name: "Holiday",
        start: "2026-10-12",
        end: null,
        allday: true,
        location: null,
        description: null,
      },
      calendar,
      3,
    );

    expect(event).toMatchObject({
      id: "xhttp://h#3",
      title: "Holiday",
      allDay: true,
      color: COLORS.external,
      extendedProps: { kind: "external", calendar },
    });
  });
});

describe("rangeFromDatesSet", () => {
  it("turns the exclusive end into the last visible day", () => {
    expect(
      rangeFromDatesSet({ start: new Date(2026, 8, 28), end: new Date(2026, 10, 9) }),
    ).toEqual({ date_from: "2026-09-28", date_to: "2026-11-08" });
  });
});

describe("earliestHour", () => {
  it("returns the earliest timed hour and ignores all-day rows", () => {
    const rows = [
      row({ start: new Date(2026, 9, 3, 14).toISOString() }),
      row({ start: new Date(2026, 9, 3, 9).toISOString() }),
      row({ start: new Date(2026, 9, 3, 1).toISOString(), allday: true }),
    ];
    expect(earliestHour(rows)).toBe(9);
  });

  it("returns null without timed rows", () => {
    expect(earliestHour([])).toBeNull();
    expect(earliestHour([row({ allday: true })])).toBeNull();
  });
});

describe("filterToQuery", () => {
  it("only keeps exclude_recurring for the empty filter", () => {
    expect(filterToQuery(emptyFilter())).toEqual({ exclude_recurring: true });
  });

  it("drops the distance without a coordinate", () => {
    const filter = { ...emptyFilter(), distance: 5000 };
    expect(filterToQuery(filter)).not.toHaveProperty("distance");
  });

  it("maps every set value", () => {
    const query = filterToQuery({
      category_id: [1, 2],
      postal_code: " 38640 ",
      coordinate: "51.9,10.4",
      location_name: "Goslar",
      distance: 5000,
      expected_participants_min: 0,
      exclude_recurring: false,
    });
    expect(query).toEqual({
      category_id: [1, 2],
      postal_code: "38640",
      coordinate: "51.9,10.4",
      distance: 5000,
      expected_participants_min: 0,
      exclude_recurring: false,
    });
  });
});
