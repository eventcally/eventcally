import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { apiParams, dateOnly, pageUrl, parseLegacyQuery, searchUrl } from "./legacyQuery";

describe("legacyQuery", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-11-01T12:00:00"));
  });
  afterEach(() => vi.useRealTimers());

  it("defaults to today without a query", () => {
    expect(parseLegacyQuery("")).toEqual({
      dateFrom: "2026-11-01",
      dateTo: "",
      categoryId: 0,
      keyword: "",
      tag: "",
      page: 1,
      perPage: null,
      styles: { s_ft: "", s_bg: "", s_pr: "", s_li: "" },
    });
  });

  it("reads the filters, the tag, the paging and the styles", () => {
    const query = parseLegacyQuery(
      "?s_ft=Verdana&s_li=%237b2424&date_from=2040-04-01 10:00:00&date_to=2040-05-01T10:00&category_id=3&keyword=Jam&tag=music&page=2&per_page=5",
    );
    expect(query).toMatchObject({
      dateFrom: "2040-04-01",
      dateTo: "2040-05-01",
      categoryId: 3,
      keyword: "Jam",
      tag: "music",
      page: 2,
      perPage: 5,
      styles: { s_ft: "Verdana", s_bg: "", s_pr: "", s_li: "#7b2424" },
    });
  });

  it("shows no lower bound for an empty date_from", () => {
    expect(parseLegacyQuery("?date_from=&keyword=x")).toMatchObject({
      dateFrom: "",
      keyword: "x",
    });
  });

  it.each([
    "?date_from=garbage&keyword=x",
    "?date_to=2040-13-45&keyword=x",
    "?category_id=abc&keyword=x",
  ])("ignores every filter when one is invalid (%s)", (search) => {
    expect(parseLegacyQuery(search)).toMatchObject({
      dateFrom: "2026-11-01",
      dateTo: "",
      categoryId: 0,
      keyword: "",
    });
  });

  it("falls back to page 1 for a bad page and ignores a bad per_page", () => {
    expect(parseLegacyQuery("?page=abc&per_page=0")).toMatchObject({
      page: 1,
      perPage: null,
    });
  });

  it("parses dates strictly", () => {
    expect(dateOnly("2040-02-30")).toBeNull();
    expect(dateOnly("")).toBeNull();
    expect(dateOnly(null)).toBeNull();
    expect(dateOnly("2040-02-29")).toBe("2040-02-29");
  });

  it("forwards what the URL says to the BFF", () => {
    expect(apiParams("?date_from=x&keyword=Jam&s_ft=Arial&page=2&per_page=3&other=1")).toEqual({
      date_from: "x",
      keyword: "Jam",
      page: "2",
      per_page: "3",
    });
    expect(apiParams("")).toEqual({});
  });

  it("builds the search URL in the legacy order", () => {
    const url = searchUrl(
      "/organizations/5/widget/eventdates",
      { dateFrom: "2040-01-01", dateTo: "", categoryId: 0, keyword: "a b" },
      {
        styles: { s_ft: "Verdana", s_bg: "", s_pr: "", s_li: "" },
        tag: "",
        perPage: null,
      },
    );
    expect(url).toBe(
      "/organizations/5/widget/eventdates?s_ft=Verdana&s_bg=&s_pr=&s_li=&date_from=2040-01-01&date_to=&category_id=0&keyword=a+b",
    );
  });

  it("keeps tag and per_page in the search URL", () => {
    const url = searchUrl(
      "/p",
      { dateFrom: "", dateTo: "", categoryId: 2, keyword: "" },
      {
        styles: { s_ft: "", s_bg: "", s_pr: "", s_li: "" },
        tag: "music",
        perPage: 3,
      },
    );
    expect(url).toContain("category_id=2&keyword=&tag=music&per_page=3");
  });

  it("sets the page in place or appends it", () => {
    expect(pageUrl("/p", "?keyword=a&page=2&date_from=x", 3)).toBe(
      "/p?keyword=a&page=3&date_from=x",
    );
    expect(pageUrl("/p", "", 2)).toBe("/p?page=2");
  });
});
