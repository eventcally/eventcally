import { describe, expect, it } from "vitest";
import { formatDate, formatDateTime, formatEventDate, formatFileSize, formatStart } from "./format";

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

describe("formatEventDate", () => {
  it("shows date and time for a timed date", () => {
    const text = formatEventDate("2026-10-03T10:00:00", null, false, "en");
    expect(text).toContain("October 3, 2026");
    expect(text).toMatch(/10:00/);
  });

  it("omits the time for all-day dates", () => {
    const text = formatEventDate("2026-10-03T00:00:00", null, true, "en");
    expect(text).toContain("October 3, 2026");
    expect(text).not.toMatch(/\d:\d\d/);
  });

  it("appends only the end time on the same day", () => {
    const text = formatEventDate("2026-10-03T10:00:00", "2026-10-03T12:30:00", false, "en");
    expect(text).toMatch(/10:00.* - 12:30/);
    expect(text.match(/2026/g)).toHaveLength(1);
  });

  it("appends the end date on another day", () => {
    const text = formatEventDate("2026-10-03T10:00:00", "2026-10-04T12:30:00", false, "en");
    expect(text).toContain("October 4, 2026");
  });

  it("shows no separator for a one-day all-day date", () => {
    const text = formatEventDate("2026-10-03T00:00:00", "2026-10-03T00:00:00", true, "en");
    expect(text).not.toContain(" - ");
  });
});

describe("formatStart", () => {
  it("joins date and time without a comma and leaves the time out when all-day", () => {
    const iso = new Date(2026, 0, 8, 10, 30).toISOString();
    expect(formatStart(iso, false, "de")).toBe("08.01.26 10:30");
    expect(formatStart(iso, true, "de")).toBe("08.01.26");
    expect(formatStart(null, false, "de")).toBe("");
  });
});

describe("formatFileSize", () => {
  it("mirrors the human_file_size Jinja filter", () => {
    expect(formatFileSize(0)).toBe("0 bytes");
    expect(formatFileSize(512)).toBe("512 bytes");
    expect(formatFileSize(1023)).toBe("1023 bytes");
    expect(formatFileSize(1024)).toBe("1KB");
    expect(formatFileSize(2048)).toBe("2KB");
    expect(formatFileSize(1536)).toBe("1KB");
    expect(formatFileSize(5 * 1024 ** 2)).toBe("5MB");
    expect(formatFileSize(3 * 1024 ** 3)).toBe("3GB");
  });
});
