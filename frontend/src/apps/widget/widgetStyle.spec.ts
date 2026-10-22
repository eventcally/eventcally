import { describe, expect, it } from "vitest";
import { defaultSettings } from "@/shared/customWidget";
import { safeCssValue, searchWidgetCss } from "./widgetStyle";

describe("safeCssValue", () => {
  it.each(["#ffffff", "#00000020", "1rem", "rgb(0, 10, 20)", "'Open Sans', sans-serif", 12])(
    "keeps %s",
    (value) => expect(safeCssValue(value)).toBe(String(value)),
  );

  it.each([
    "red; } body { display: none",
    "red}",
    "url(http://evil.example/x.png)",
    "</style><script>",
    "red\\00",
    "'unbalanced",
    "",
    "   ",
    null,
    undefined,
    {},
  ])("drops %j", (value) => expect(safeCssValue(value)).toBeNull());
});

describe("searchWidgetCss", () => {
  const css = searchWidgetCss(defaultSettings("search", null));

  it("maps the settings to the Bootstrap 5 selectors", () => {
    expect(css).toContain("body {\n  background-color: #ffffff;\n  color: #212529;");
    expect(css).toContain(".pagination .page-item.active .page-link");
    expect(css).toContain(".badge.text-bg-warning {\n  background-color: #ffc107 !important;");
    expect(css).toContain(".badge.text-bg-info");
    expect(css).toContain("--bs-btn-bg: #007bff;");
    expect(css).toContain(".btn-secondary {\n  --bs-btn-bg: #6c757d;");
    expect(css).toContain(".card-subtitle.text-body {\n  color: #212529 !important;");
    expect(css).toContain(".form-select");
    expect(css).toContain("a, a:hover {\n  color: #007bff;");
  });

  it("omits an empty font family", () => {
    expect(css).not.toContain("font-family");
  });

  it("drops injected values but keeps the rest", () => {
    const hostile = {
      ...defaultSettings("search", null),
      background: "red; } * { display: none",
      linkColor: "#123456",
      fontFamily: "'Open Sans', sans-serif",
    };
    const result = searchWidgetCss(hostile);

    expect(result).not.toContain("display");
    expect(result).toContain("color: #123456;");
    expect(result).toContain("font-family: 'Open Sans', sans-serif;");
    expect(result).not.toContain("background-color: red");
  });
});
