// The stored settings of a search widget become CSS here. They are user input shown on third-party
// sites, so every value passes an allow-list; a value that does not match is dropped.
import type { SearchSettings } from "@/shared/customWidget";

const SAFE_VALUE = /^[#\w\s,.%()'"-]*$/;

/** Colour, length and font tokens only; no `;{}:/\@<` that could end the declaration or the rule. */
export function safeCssValue(value: unknown): string | null {
  if (typeof value !== "string" && typeof value !== "number") return null;
  const text = String(value).trim();
  if (!text || !SAFE_VALUE.test(text)) return null;
  // An unbalanced quote would swallow the rest of the stylesheet.
  if ((text.match(/'/g)?.length ?? 0) % 2 || (text.match(/"/g)?.length ?? 0) % 2) return null;
  return text;
}

function rule(selector: string, declarations: [string, unknown, string?][]): string {
  const body = declarations
    .map(([property, value, suffix]) => {
      const safe = safeCssValue(value);
      return safe == null ? null : `  ${property}: ${safe}${suffix ?? ""};`;
    })
    .filter((line): line is string => line != null);
  return body.length ? `${selector} {\n${body.join("\n")}\n}` : "";
}

export function searchWidgetCss(s: SearchSettings): string {
  const button = (selector: string, bg: unknown, border: unknown, text: unknown) =>
    rule(selector, [
      ["--bs-btn-bg", bg],
      ["--bs-btn-border-color", border],
      ["--bs-btn-color", text],
      ["--bs-btn-hover-bg", bg],
      ["--bs-btn-hover-border-color", border],
      ["--bs-btn-hover-color", text],
      ["--bs-btn-active-bg", bg],
      ["--bs-btn-active-border-color", border],
      ["--bs-btn-active-color", text],
      ["--bs-btn-disabled-bg", bg],
      ["--bs-btn-disabled-border-color", border],
      ["--bs-btn-disabled-color", text],
    ]);

  return [
    rule("body", [
      ["background-color", s.background],
      ["color", s.textColor],
      ["font-family", s.fontFamily],
      ["padding", s.padding],
    ]),
    rule(".pagination .page-link", [
      ["background-color", s.background],
      ["border-color", s.pagingBorderColor],
      ["color", s.pagingColor],
    ]),
    rule(".pagination .page-link:hover", [
      ["background-color", s.pagingColor],
      ["border-color", s.pagingColor],
      ["color", s.pagingActiveTextColor],
    ]),
    rule(".pagination .page-item.active .page-link", [
      ["background-color", s.pagingColor],
      ["border-color", s.pagingColor],
      ["color", s.pagingActiveTextColor],
    ]),
    rule(".pagination .page-item.disabled .page-link", [
      ["background-color", s.background],
      ["border-color", s.pagingBorderColor],
      ["color", s.pagingDisabledTextColor],
    ]),
    button(".btn-primary", s.buttonBackgroundColor, s.buttonBorderColor, s.buttonTextColor),
    button(
      ".btn-secondary",
      s.printButtonBackgroundColor,
      s.printButtonBorderColor,
      s.printButtonTextColor,
    ),
    rule(".input-group-text", [
      ["background-color", s.filterLabelBackgroundColor],
      ["border-color", s.filterLabelBorderColor],
      ["color", s.filterLabelTextColor],
    ]),
    rule(".form-control, .form-control:focus, .form-select, .form-select:focus", [
      ["background-color", s.filterInputBackgroundColor],
      ["border-color", s.filterInputBorderColor],
      ["color", s.filterInputTextColor],
    ]),
    rule(".card", [
      ["--bs-card-bg", s.eventBackgroundColor],
      ["--bs-card-border-color", s.eventBorderColor],
      ["background-color", s.eventBackgroundColor],
      ["border-color", s.eventBorderColor],
    ]),
    rule(".card-title", [["color", s.eventNameTextColor]]),
    rule(".card-subtitle.text-body", [["color", s.eventDateTextColor, " !important"]]),
    rule(".card .text-muted", [["color", s.eventInfoTextColor, " !important"]]),
    rule(".badge.text-bg-warning", [
      ["background-color", s.eventBadgeWarningBackgroundColor, " !important"],
      ["color", s.eventBadgeWarningTextColor, " !important"],
    ]),
    rule(".badge.text-bg-info", [
      ["background-color", s.eventBadgeInfoBackgroundColor, " !important"],
      ["color", s.eventBadgeInfoTextColor, " !important"],
    ]),
    rule("a, a:hover", [["color", s.linkColor]]),
    "a.underlined {\n  text-decoration: underline;\n}",
  ]
    .filter(Boolean)
    .join("\n\n");
}
