import { describe, expect, it } from "vitest";
import {
  emptyFilter,
  fromRouteQuery,
  hasExtendedFilter,
  toBffParams,
  toRouteQuery,
} from "./manageEventQuery";

const defaults = { date_from: "2030-10-01" };

describe("manageEventQuery", () => {
  it("starts at the default date and leaves defaults out of the URL", () => {
    const filter = emptyFilter(defaults);
    expect(filter.date_from).toBe("2030-10-01");
    expect(toRouteQuery(filter, defaults)).toEqual({});
  });

  it("round-trips a filter through the URL", () => {
    const filter = {
      ...emptyFilter(defaults),
      keyword: " Jam ",
      date_from: "2030-11-01",
      date_to: "2030-11-30",
      category_id: 3,
      tag: "music,live",
      internal_tag: "secret",
      organizer_id: 4,
      event_place_id: 5,
      postal_code: "38640,38690",
      radius_coordinate: "51.9,10.4",
      radius_location_name: "Goslar",
      radius_distance: 500,
      status: 2,
      public_status: 1,
      created_at_from: "2030-01-01",
      created_at_to: "2030-01-31",
      is_recurring: "1" as const,
      sort: "-created_at" as const,
      page: 2,
    };

    const query = toRouteQuery(filter, defaults) as Record<string, string>;

    expect(query.keyword).toBe("Jam");
    expect(fromRouteQuery(query, defaults)).toEqual({ ...filter, keyword: "Jam" });
  });

  it("reads a legacy place link", () => {
    const filter = fromRouteQuery({ event_place_id: "5" }, defaults);
    expect(filter.event_place_id).toBe(5);
    expect(filter.date_from).toBe("2030-10-01");
    expect(hasExtendedFilter(filter)).toBe(true);
  });

  it("reads a legacy organizer link and comma separated tags", () => {
    const filter = fromRouteQuery({ organizer_id: "7", tag: "a,b" }, defaults);
    expect(filter.organizer_id).toBe(7);
    expect(filter.tag).toBe("a,b");
  });

  it("falls back for unusable values", () => {
    const filter = fromRouteQuery(
      {
        date_from: "03.10.2020",
        date_to: "",
        status: "-1",
        public_status: "x",
        is_recurring: "2",
        sort: "name",
        page: "0",
        category_id: "0",
      },
      defaults,
    );
    expect(filter).toEqual(emptyFilter(defaults));
  });

  it("needs a coordinate for the radius", () => {
    const withDistance = fromRouteQuery({ radius_distance: "500" }, defaults);
    expect(withDistance.radius_distance).toBeNull();

    const full = fromRouteQuery(
      {
        radius_coordinate: "51.9077888,10.4333312",
        radius_distance: "500",
        radius_location_name: "Aktuelle Position",
      },
      defaults,
    );
    expect(full.radius_distance).toBe(500);
    expect(full.radius_location_name).toBe("Aktuelle Position");
    expect(fromRouteQuery({ radius_coordinate: "nope" }, defaults).radius_coordinate).toBe("");
  });

  it("builds the BFF params without empty values", () => {
    expect(toBffParams(emptyFilter(defaults))).toEqual({
      page: 1,
      date_from: "2030-10-01",
      sort: "min_start",
    });

    const params = toBffParams({
      ...emptyFilter(defaults),
      radius_coordinate: "51.9,10.4",
      radius_distance: null,
      is_recurring: "0",
      status: 2,
    });
    expect(params.radius_coordinate).toBeUndefined();
    expect(params.is_recurring).toBe("0");
    expect(params.status).toBe(2);
  });

  it("expands only for filters outside the always visible row", () => {
    expect(hasExtendedFilter(emptyFilter(defaults))).toBe(false);
    expect(hasExtendedFilter({ ...emptyFilter(defaults), keyword: "x", date_to: "2030-12-01" })).toBe(
      false,
    );
    expect(hasExtendedFilter({ ...emptyFilter(defaults), is_recurring: "0" })).toBe(true);
  });
});
