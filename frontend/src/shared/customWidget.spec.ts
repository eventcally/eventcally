import { describe, expect, it } from "vitest";
import {
  calendarFields,
  defaultSettings,
  installationBody,
  installationHeader,
  mergeSettings,
  previewResizerOptions,
  searchFields,
  type SearchSettings,
} from "./customWidget";

const t = (key: string) => key;

describe("defaultSettings", () => {
  it("has the stored search keys", () => {
    const settings = defaultSettings("search", 7);
    expect(Object.keys(settings)).toHaveLength(41);
    expect(settings).toMatchObject({
      layout: "card",
      iFrameMinHeight: 400,
      iFrameMaxHeight: "Infinity",
      iFrameAutoResize: true,
      organizationId: 7,
      eventsPerPage: 10,
      linkColor: "#007bff",
      eventBorderColor: "#00000020",
    });
  });

  it("has the stored calendar keys", () => {
    expect(defaultSettings("calendar", null)).toEqual({
      iFrameHeight: 600,
      iFrameAutoResize: false,
      organizationId: null,
      calendarType: "week",
      eventBackgroundColor: "#007bff",
    });
  });
});

describe("mergeSettings", () => {
  it("lets stored values win and keeps unknown keys", () => {
    const merged = mergeSettings(defaultSettings("calendar", 1), {
      calendarType: "month",
      legacyKey: "x",
    });
    expect(merged).toMatchObject({
      calendarType: "month",
      iFrameHeight: 600,
      legacyKey: "x",
    });
  });

  it("tolerates missing stored settings", () => {
    expect(mergeSettings({ a: 1 }, null)).toEqual({ a: 1 });
  });
});

describe("field descriptors", () => {
  const defaults = defaultSettings("search", 1);
  const visible = (settings: SearchSettings) =>
    searchFields.filter((f) => !f.visibleIf || f.visibleIf(settings)).map((f) => f.key);

  it("covers every search setting except the ones the form does not edit", () => {
    const keys = searchFields.map((f) => f.key);
    const missing = Object.keys(defaults).filter((k) => !keys.includes(k as keyof SearchSettings));
    expect(missing.sort()).toEqual(["iFrameAutoResize", "organizationId"]);
  });

  it("hides colours of switched-off parts", () => {
    const off = {
      ...defaults,
      layout: "text",
      showFilter: false,
      showPagination: false,
    } as SearchSettings;
    expect(visible(off)).not.toContain("eventBackgroundColor");
    expect(visible(off)).not.toContain("filterLabelTextColor");
    expect(visible(off)).not.toContain("pagingColor");
    expect(visible(off)).not.toContain("printButtonTextColor");
    expect(visible({ ...off, showPrintButton: true })).toContain("printButtonTextColor");
    expect(visible(defaults)).toContain("eventBackgroundColor");
    expect(visible(defaults)).toContain("pagingActiveTextColor");
  });

  it("builds composite labels", () => {
    const field = searchFields.find((f) => f.key === "pagingDisabledTextColor")!;
    expect(field.label(t)).toBe("Pagination Deactivated Text color");
    expect(calendarFields.find((f) => f.key === "eventBackgroundColor")!.label(t)).toBe(
      "Event color",
    );
  });

  it("debounces the height inputs", () => {
    expect(searchFields.filter((f) => f.debounce).map((f) => f.key)).toEqual([
      "iFrameMinHeight",
      "iFrameMaxHeight",
    ]);
  });
});

describe("installation", () => {
  it("names the loader of the origin", () => {
    const header = installationHeader("https://example.org");
    expect(header).toContain("'https://example.org/static/widget-loader.js'");
    expect(header.startsWith("<!-- Event calendar widget -->")).toBe(true);
  });

  it("renders the placeholder", () => {
    expect(installationBody(5)).toBe('<div class="eventcally-widget" data-widget-id="5"></div>');
  });
});

describe("previewResizerOptions", () => {
  it("reads min and max height of the search widget", () => {
    expect(previewResizerOptions(defaultSettings("search", null))).toEqual({
      autoResize: true,
      minHeight: 400,
      maxHeight: "Infinity",
    });
  });

  it("uses the calendar height for both", () => {
    expect(previewResizerOptions(defaultSettings("calendar", null))).toEqual({
      autoResize: false,
      minHeight: 600,
      maxHeight: 600,
    });
  });
});
