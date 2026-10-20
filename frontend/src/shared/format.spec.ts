import { describe, expect, it } from "vitest";
import { formatDate, formatDateTime } from "./format";

describe("formatDateTime", () => {
  it("returns an empty string for missing values", () => {
    expect(formatDateTime(null, "de")).toBe("");
    expect(formatDateTime(undefined, "de")).toBe("");
  });

  it("formats an ISO date for the locale", () => {
    expect(formatDateTime("2026-01-02T13:45:00", "en")).toContain("2026");
  });
});

describe("formatDate", () => {
  it("returns an empty string for missing values", () => {
    expect(formatDate(null, "de")).toBe("");
  });

  it("formats the date without time", () => {
    expect(formatDate("2026-10-08T14:49:00", "de")).toBe("08.10.2026");
  });
});
