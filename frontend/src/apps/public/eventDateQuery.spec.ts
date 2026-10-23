import { describe, expect, it } from "vitest";
import {
  emptyFilter,
  fromRouteQuery,
  hasExtendedFilter,
  toBffParams,
  toRouteQuery,
} from "./eventDateQuery";

const defaults = { date_from: "2030-10-01" };

describe("eventDateQuery", () => {
  it("falls back to the defaults for an empty URL", () => {
    expect(fromRouteQuery({}, defaults)).toEqual(emptyFilter(defaults));
  });

  it("reads the legacy parameters", () => {
    const filter = fromRouteQuery(
      {
        date_from: "2030-11-01",
        date_to: "2030-11-30",
        keyword: " jam ",
        category_id: "3",
        tag: "live",
        admin_unit_id: "7",
        organizer_id: "9",
        postal_code: "38640",
        coordinate: "51.9,10.4",
        location: "Goslar",
        distance: "5000",
        created_at_from: "2030-01-01",
        created_at_to: "2030-02-01",
        sort: "-created_at",
        exclude_recurring: "y",
        not_referenced: "1",
        page: "2",
      },
      defaults,
    );

    expect(filter).toEqual({
      date_from: "2030-11-01",
      date_to: "2030-11-30",
      keyword: "jam",
      category_id: 3,
      tag: "live",
      admin_unit_id: 7,
      organizer_id: 9,
      postal_code: "38640",
      coordinate: "51.9,10.4",
      location: "Goslar",
      distance: 5000,
      created_at_from: "2030-01-01",
      created_at_to: "2030-02-01",
      sort: "-created_at",
      exclude_recurring: true,
      not_referenced: true,
      page: 2,
    });
  });

  it("treats category 0 as any and ignores invalid values", () => {
    const filter = fromRouteQuery(
      { category_id: "0", date_from: "tomorrow", admin_unit_id: "x", page: "-3", sort: "foo" },
      defaults,
    );

    expect(filter.category_id).toBeNull();
    expect(filter.date_from).toBe(defaults.date_from);
    expect(filter.admin_unit_id).toBeNull();
    expect(filter.page).toBe(1);
    expect(filter.sort).toBe("start");
  });

  it("drops the distance without a coordinate", () => {
    const filter = fromRouteQuery({ distance: "500", location: "Goslar" }, defaults);

    expect(filter.distance).toBeNull();
    expect(filter.location).toBe("");
    expect(fromRouteQuery({ coordinate: "oops", distance: "500" }, defaults).coordinate).toBe("");
  });

  it("omits defaults and empty values when writing the URL", () => {
    expect(toRouteQuery(emptyFilter(defaults), defaults)).toEqual({});

    const filter = {
      ...emptyFilter(defaults),
      date_from: "2030-12-01",
      keyword: "jam ",
      category_id: 3,
      coordinate: "51.9,10.4",
      location: "Goslar",
      distance: 500,
      sort: "-created_at" as const,
      exclude_recurring: true,
      page: 3,
    };
    expect(toRouteQuery(filter, defaults)).toEqual({
      date_from: "2030-12-01",
      keyword: "jam",
      category_id: "3",
      coordinate: "51.9,10.4",
      location: "Goslar",
      distance: "500",
      sort: "-created_at",
      exclude_recurring: "1",
      page: "3",
    });
  });

  it("round trips", () => {
    const filter = {
      ...emptyFilter(defaults),
      date_to: "2030-12-31",
      organizer_id: 4,
      admin_unit_id: 2,
      not_referenced: true,
      page: 2,
    };

    expect(fromRouteQuery(toRouteQuery(filter, defaults) as never, defaults)).toEqual(filter);
  });

  it("builds the BFF params", () => {
    const params = toBffParams({
      ...emptyFilter(defaults),
      keyword: " jam ",
      category_id: 3,
      coordinate: "51.9,10.4",
      distance: 500,
    });

    expect(params).toMatchObject({
      page: 1,
      date_from: "2030-10-01",
      keyword: "jam",
      category_id: [3],
      coordinate: "51.9,10.4",
      distance: 500,
      sort: "start",
      date_to: undefined,
      exclude_recurring: undefined,
    });
  });

  it("detects extended filters", () => {
    expect(hasExtendedFilter(emptyFilter(defaults))).toBe(false);
    expect(hasExtendedFilter({ ...emptyFilter(defaults), keyword: "x", date_to: "2030-12-01" })).toBe(false);
    expect(hasExtendedFilter({ ...emptyFilter(defaults), tag: "x" })).toBe(true);
    expect(hasExtendedFilter({ ...emptyFilter(defaults), not_referenced: true })).toBe(true);
  });
});
