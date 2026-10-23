// Model of the custom widgets, shared by the configurator (manage) and the embedded widget pages.
// The settings keys and their defaults are a wire contract: they are stored as JSON in
// `custom_widget.settings` and read by widgets embedded on customer sites.

export type WidgetType = "search" | "calendar";
export type Translate = (key: string) => string;

export interface SearchSettings {
  layout: "card" | "text";
  iFrameMinHeight: number | string;
  iFrameMaxHeight: number | string;
  iFrameAutoResize: boolean;
  organizationId: number | string | null;
  eventsPerPage: number | string;
  showFilter: boolean;
  showPagination: boolean;
  showPrintButton: boolean;
  showEventCallyLink: boolean;
  fontFamily: string;
  background: string;
  textColor: string;
  padding: string;
  linkColor: string;
  buttonBackgroundColor: string;
  buttonBorderColor: string;
  buttonTextColor: string;
  printButtonBackgroundColor: string;
  printButtonBorderColor: string;
  printButtonTextColor: string;
  filterLabelBackgroundColor: string;
  filterLabelBorderColor: string;
  filterLabelTextColor: string;
  filterInputBackgroundColor: string;
  filterInputBorderColor: string;
  filterInputTextColor: string;
  eventBackgroundColor: string;
  eventBorderColor: string;
  eventNameTextColor: string;
  eventDateTextColor: string;
  eventInfoTextColor: string;
  pagingBorderColor: string;
  pagingColor: string;
  pagingTextColor: string;
  pagingActiveTextColor: string;
  pagingDisabledTextColor: string;
  eventBadgeWarningBackgroundColor: string;
  eventBadgeWarningTextColor: string;
  eventBadgeInfoBackgroundColor: string;
  eventBadgeInfoTextColor: string;
}

export interface CalendarSettings {
  iFrameHeight: number | string;
  iFrameAutoResize: boolean;
  organizationId: number | string | null;
  calendarType: "week" | "month";
  eventBackgroundColor: string;
}

export interface SettingsByType {
  search: SearchSettings;
  calendar: CalendarSettings;
}

export type Settings = SearchSettings | CalendarSettings;

export function defaultSettings<T extends WidgetType>(
  type: T,
  organizationId: number | string | null,
): SettingsByType[T];
export function defaultSettings(
  type: WidgetType,
  organizationId: number | string | null,
): Settings {
  if (type === "calendar") {
    return {
      iFrameHeight: 600,
      iFrameAutoResize: false,
      organizationId,
      calendarType: "week",
      eventBackgroundColor: "#007bff",
    };
  }

  return {
    layout: "card",
    iFrameMinHeight: 400,
    iFrameMaxHeight: "Infinity",
    iFrameAutoResize: true,
    organizationId,
    eventsPerPage: 10,
    showFilter: true,
    showPagination: true,
    showPrintButton: false,
    showEventCallyLink: true,
    fontFamily: "",
    background: "#ffffff",
    textColor: "#212529",
    padding: "1rem",
    linkColor: "#007bff",
    buttonBackgroundColor: "#007bff",
    buttonBorderColor: "#007bff",
    buttonTextColor: "#ffffff",
    printButtonBackgroundColor: "#6c757d",
    printButtonBorderColor: "#6c757d",
    printButtonTextColor: "#ffffff",
    filterLabelBackgroundColor: "#e9ecef",
    filterLabelBorderColor: "#ced4da",
    filterLabelTextColor: "#495057",
    filterInputBackgroundColor: "#ffffff",
    filterInputBorderColor: "#ced4da",
    filterInputTextColor: "#495057",
    eventBackgroundColor: "#ffffff",
    eventBorderColor: "#00000020",
    eventNameTextColor: "#000000",
    eventDateTextColor: "#212529",
    eventInfoTextColor: "#6c757d",
    pagingBorderColor: "#dee2e6",
    pagingColor: "#007bff",
    pagingTextColor: "#007bff",
    pagingActiveTextColor: "#ffffff",
    pagingDisabledTextColor: "#6c757d",
    eventBadgeWarningBackgroundColor: "#ffc107",
    eventBadgeWarningTextColor: "#212529",
    eventBadgeInfoBackgroundColor: "#17a2b8",
    eventBadgeInfoTextColor: "#ffffff",
  };
}

/** Stored values win over the defaults; stored keys the defaults do not know are kept. */
export function mergeSettings<T extends object>(
  defaults: T,
  stored: Record<string, unknown> | null | undefined,
): T {
  return { ...defaults, ...(stored ?? {}) };
}

export type FieldKind = "select" | "number" | "text" | "checkbox" | "color";

export interface FieldDescriptor<S> {
  key: keyof S & string;
  tab: "settings" | "styles";
  kind: FieldKind;
  label: (t: Translate) => string;
  /** Text inputs that move the iframe size are debounced by the form. */
  debounce?: boolean;
  visibleIf?: (settings: S) => boolean;
}

// Literal translate calls only: the gettext extractor does not see msgids passed as arguments.
const subject = {
  event: (t: Translate) => t("Event"),
  eventName: (t: Translate) => t("Event name"),
  eventDate: (t: Translate) => t("Event date"),
  eventInfo: (t: Translate) => t("Event info"),
  badgeWarning: (t: Translate) => t("Event warning badge"),
  badgeInfo: (t: Translate) => t("Event info badge"),
  filterLabel: (t: Translate) => t("Filter label"),
  filterInput: (t: Translate) => t("Filter input"),
  filterButton: (t: Translate) => t("Filter button"),
  pagination: (t: Translate) => t("Pagination"),
  printButton: (t: Translate) => t("Print button"),
};
const property = {
  background: (t: Translate) => t("Background color"),
  border: (t: Translate) => t("Border color"),
  text: (t: Translate) => t("Text color"),
  color: (t: Translate) => t("Color"),
  disabledText: (t: Translate) => `${t("Deactivated")} ${t("Text color")}`,
  activeText: (t: Translate) => `${t("Active")} ${t("Text color")}`,
};
type Part = (t: Translate) => string;

const colorLabel = (first: Part, second: Part) => (t: Translate) => `${first(t)} ${second(t)}`;

function color<S>(
  key: keyof S & string,
  label: (t: Translate) => string,
  visibleIf?: (settings: S) => boolean,
): FieldDescriptor<S> {
  return { key, tab: "styles", kind: "color", label, visibleIf };
}

const isCard = (s: SearchSettings) => s.layout === "card";
const hasFilter = (s: SearchSettings) => s.showFilter;
const hasPagination = (s: SearchSettings) => s.showPagination;
const hasPrint = (s: SearchSettings) => s.showPrintButton;

export const searchFields: FieldDescriptor<SearchSettings>[] = [
  { key: "layout", tab: "settings", kind: "select", label: (t) => t("Layout") },
  {
    key: "eventsPerPage",
    tab: "settings",
    kind: "number",
    label: (t) => t("Events per page"),
  },
  {
    key: "showFilter",
    tab: "settings",
    kind: "checkbox",
    label: (t) => t("Filter"),
  },
  {
    key: "showPagination",
    tab: "settings",
    kind: "checkbox",
    label: (t) => t("Pagination"),
  },
  {
    key: "showEventCallyLink",
    tab: "settings",
    kind: "checkbox",
    label: (t) => t("Link"),
  },
  {
    key: "showPrintButton",
    tab: "settings",
    kind: "checkbox",
    label: (t) => t("Print button"),
  },
  {
    key: "iFrameMinHeight",
    tab: "settings",
    kind: "text",
    debounce: true,
    label: (t) => t("Min. height"),
  },
  {
    key: "iFrameMaxHeight",
    tab: "settings",
    kind: "text",
    debounce: true,
    label: (t) => t("Max. height"),
  },

  {
    key: "fontFamily",
    tab: "styles",
    kind: "text",
    label: (t) => t("Font family"),
  },
  { key: "padding", tab: "styles", kind: "text", label: (t) => t("Padding") },
  color("background", (t) => t("Background color")),
  color("textColor", (t) => t("Text color")),
  color("linkColor", (t) => t("Link color")),

  color("eventBackgroundColor", colorLabel(subject.event, property.background), isCard),
  color("eventBorderColor", colorLabel(subject.event, property.border), isCard),
  color("eventNameTextColor", colorLabel(subject.eventName, property.text), isCard),
  color("eventDateTextColor", colorLabel(subject.eventDate, property.text), isCard),
  color("eventInfoTextColor", colorLabel(subject.eventInfo, property.text), isCard),

  color("eventBadgeWarningBackgroundColor", colorLabel(subject.badgeWarning, property.background)),
  color("eventBadgeWarningTextColor", colorLabel(subject.badgeWarning, property.text)),
  color("eventBadgeInfoBackgroundColor", colorLabel(subject.badgeInfo, property.background)),
  color("eventBadgeInfoTextColor", colorLabel(subject.badgeInfo, property.text)),

  color(
    "filterLabelBackgroundColor",
    colorLabel(subject.filterLabel, property.background),
    hasFilter,
  ),
  color("filterLabelBorderColor", colorLabel(subject.filterLabel, property.border), hasFilter),
  color("filterLabelTextColor", colorLabel(subject.filterLabel, property.text), hasFilter),
  color(
    "filterInputBackgroundColor",
    colorLabel(subject.filterInput, property.background),
    hasFilter,
  ),
  color("filterInputBorderColor", colorLabel(subject.filterInput, property.border), hasFilter),
  color("filterInputTextColor", colorLabel(subject.filterInput, property.text), hasFilter),
  color("buttonBackgroundColor", colorLabel(subject.filterButton, property.background), hasFilter),
  color("buttonBorderColor", colorLabel(subject.filterButton, property.border), hasFilter),
  color("buttonTextColor", colorLabel(subject.filterButton, property.text), hasFilter),

  color("pagingBorderColor", colorLabel(subject.pagination, property.border), hasPagination),
  color("pagingColor", colorLabel(subject.pagination, property.color), hasPagination),
  color("pagingTextColor", colorLabel(subject.pagination, property.text), hasPagination),
  color(
    "pagingDisabledTextColor",
    colorLabel(subject.pagination, property.disabledText),
    hasPagination,
  ),
  color(
    "pagingActiveTextColor",
    colorLabel(subject.pagination, property.activeText),
    hasPagination,
  ),

  color(
    "printButtonBackgroundColor",
    colorLabel(subject.printButton, property.background),
    hasPrint,
  ),
  color("printButtonBorderColor", colorLabel(subject.printButton, property.border), hasPrint),
  color("printButtonTextColor", colorLabel(subject.printButton, property.text), hasPrint),
];

export const calendarFields: FieldDescriptor<CalendarSettings>[] = [
  {
    key: "calendarType",
    tab: "settings",
    kind: "select",
    label: (t) => t("Calendar type"),
  },
  {
    key: "iFrameHeight",
    tab: "settings",
    kind: "text",
    debounce: true,
    label: (t) => t("Height"),
  },
  color("eventBackgroundColor", (t) => t("Event color")),
];

export function fieldsFor(type: "search"): FieldDescriptor<SearchSettings>[];
export function fieldsFor(type: "calendar"): FieldDescriptor<CalendarSettings>[];
export function fieldsFor(
  type: WidgetType,
): FieldDescriptor<SearchSettings>[] | FieldDescriptor<CalendarSettings>[];
export function fieldsFor(type: WidgetType) {
  return type === "calendar" ? calendarFields : searchFields;
}

/** The `<script>` that loads the widget on a customer site (`<head>`). */
export function installationHeader(origin: string): string {
  return (
    "<!-- Event calendar widget -->\n" +
    "<script>(function(w,d,s,o,f,js,fjs){w['EventCallyWidget']=o;w[o]=w[o]||function(){(w[o].q=w[o].q||[]).push(arguments)};js=d.createElement(s),fjs=d.getElementsByTagName(s)[0];js.id=o;js.src=f;js.async=1;fjs.parentNode.insertBefore(js,fjs);}(window,document,'script','eventcally','" +
    origin +
    "/static/widget-loader.js'));</script>\n" +
    "<!-- End event calendar widget -->"
  );
}

/** The placeholder element that shows the widget (`<body>`). */
export function installationBody(widgetId: number | string): string {
  return '<div class="eventcally-widget" data-widget-id="' + widgetId + '"></div>';
}

export interface ResizerOptions {
  autoResize: boolean;
  minHeight: number | string;
  maxHeight: number | string;
}

/** What `iFrameResize` needs for the preview; a change remounts the iframe. */
export function previewResizerOptions(settings: Settings): ResizerOptions {
  const search = settings as Partial<SearchSettings>;
  const calendar = settings as Partial<CalendarSettings>;
  return {
    autoResize: Boolean(settings.iFrameAutoResize),
    minHeight: search.iFrameMinHeight ?? calendar.iFrameHeight ?? 0,
    maxHeight: search.iFrameMaxHeight ?? calendar.iFrameHeight ?? 0,
  };
}
