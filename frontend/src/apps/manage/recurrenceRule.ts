// The recurrence rules the previous event form (`jquery.recurrenceinput.js`) writes, and
// nothing else: `RRULE:FREQ=...` with an optional `INTERVAL`, the weekdays of a weekly
// rule, a day or a weekday of the month (and the month of a yearly rule), `COUNT` or
// `UNTIL`, plus `EXDATE`/`RDATE` lines. A stored rule outside this subset does not parse
// and stays as it is.

export const FREQUENCIES = ["DAILY", "WEEKLY", "MONTHLY", "YEARLY"] as const;
// The order the legacy widget lists (and writes) the weekdays in.
export const WEEKDAYS = ["SU", "MO", "TU", "WE", "TH", "FR", "SA"] as const;
export const WEEKDAY_INDEXES = ["+1", "+2", "+3", "+4", "-1"] as const;

export type Frequency = (typeof FREQUENCIES)[number];
export type Weekday = (typeof WEEKDAYS)[number];
export type WeekdayIndex = (typeof WEEKDAY_INDEXES)[number];
export type MonthlyType = "DAYOFMONTH" | "WEEKDAYOFMONTH";

export type RecurrenceEnd =
  | { type: "never" }
  | { type: "count"; count: number }
  // `YYYY-MM-DD`.
  | { type: "until"; until: string };

export interface RecurrenceValue {
  freq: Frequency;
  interval: number;
  // Weekly.
  weekdays: Weekday[];
  // Monthly and yearly: `null` adds no day (the legacy radio left unchecked).
  monthlyType: MonthlyType | null;
  monthDay: number;
  weekdayIndex: WeekdayIndex;
  weekday: Weekday;
  // Yearly, 1-12.
  month: number;
  end: RecurrenceEnd;
  // `YYYYMMDDT000000`, sorted.
  exdates: string[];
  rdates: string[];
}

const DATE_TIME = /^\d{8}T000000$/;

/** The default rule of a frequency, starting on `start` (`YYYY-MM-DD`). */
export function defaultRecurrence(freq: Frequency, start: string): RecurrenceValue {
  const [year, month, day] = start.split("-").map(Number);
  const weekday = WEEKDAYS[new Date(year, month - 1, day).getDay()];
  return {
    freq,
    interval: 1,
    weekdays: freq === "WEEKLY" ? [weekday] : [],
    monthlyType: freq === "MONTHLY" || freq === "YEARLY" ? "DAYOFMONTH" : null,
    monthDay: day,
    weekdayIndex: "+1",
    weekday,
    month,
    end: { type: "until", until: start },
    exdates: [],
    rdates: [],
  };
}

export function toDateTime(date: string): string {
  return `${date.replaceAll("-", "")}T000000`;
}

export function fromDateTime(value: string): string {
  return `${value.slice(0, 4)}-${value.slice(4, 6)}-${value.slice(6, 8)}`;
}

export function serialize(value: RecurrenceValue): string {
  let rule = `FREQ=${value.freq}`;

  if (value.interval !== 1) rule += `;INTERVAL=${value.interval}`;

  if (value.freq === "WEEKLY") {
    const weekdays = WEEKDAYS.filter((day) => value.weekdays.includes(day));
    if (weekdays.length) rule += `;BYDAY=${weekdays.join(",")}`;
  }

  if (value.freq === "YEARLY" && value.monthlyType) rule += `;BYMONTH=${value.month}`;

  if ((value.freq === "MONTHLY" || value.freq === "YEARLY") && value.monthlyType) {
    rule +=
      value.monthlyType === "DAYOFMONTH"
        ? `;BYMONTHDAY=${value.monthDay}`
        : `;BYDAY=${value.weekdayIndex}${value.weekday}`;
  }

  if (value.end.type === "count") rule += `;COUNT=${value.end.count}`;
  if (value.end.type === "until") rule += `;UNTIL=${toDateTime(value.end.until)}`;

  let result = `RRULE:${rule}`;
  if (value.exdates.length) result += `\nEXDATE:${[...value.exdates].sort().join(",")}`;
  if (value.rdates.length) result += `\nRDATE:${[...value.rdates].sort().join(",")}`;
  return result;
}

function positiveInt(text: string | undefined): number | null {
  if (!text || !/^\d+$/.test(text)) return null;
  const number = Number(text);
  return number > 0 ? number : null;
}

function dates(text: string): string[] | null {
  const values = text.split(",");
  return values.every((value) => DATE_TIME.test(value)) ? values : null;
}

function parseLoose(rule: string): RecurrenceValue | null {
  const lines = rule.split("\n");
  if (!lines[0].startsWith("RRULE:")) return null;

  const parts = new Map<string, string>();
  for (const part of lines[0].slice("RRULE:".length).split(";")) {
    const [key, text, ...rest] = part.split("=");
    if (text === undefined || rest.length || parts.has(key)) return null;
    parts.set(key, text);
  }

  const freq = parts.get("FREQ") as Frequency;
  if (!FREQUENCIES.includes(freq)) return null;

  const value = defaultRecurrence(freq, "2000-01-01");
  value.weekdays = [];
  value.monthlyType = null;
  value.end = { type: "never" };

  for (const [key, text] of parts) {
    if (key === "FREQ") continue;

    if (key === "INTERVAL") {
      const interval = positiveInt(text);
      if (!interval) return null;
      value.interval = interval;
    } else if (key === "COUNT") {
      const count = positiveInt(text);
      if (!count) return null;
      value.end = { type: "count", count };
    } else if (key === "UNTIL") {
      if (!DATE_TIME.test(text)) return null;
      value.end = { type: "until", until: fromDateTime(text) };
    } else if (key === "BYMONTH" && freq === "YEARLY") {
      const month = positiveInt(text);
      if (!month || month > 12) return null;
      value.month = month;
    } else if (key === "BYMONTHDAY" && (freq === "MONTHLY" || freq === "YEARLY")) {
      const day = positiveInt(text);
      if (!day || day > 31) return null;
      value.monthlyType = "DAYOFMONTH";
      value.monthDay = day;
    } else if (key === "BYDAY" && freq === "WEEKLY") {
      const weekdays = text.split(",") as Weekday[];
      if (!weekdays.every((day) => WEEKDAYS.includes(day))) return null;
      value.weekdays = weekdays;
    } else if (key === "BYDAY" && (freq === "MONTHLY" || freq === "YEARLY")) {
      const match = /^([+-]\d)([A-Z]{2})$/.exec(text);
      const index = match?.[1] as WeekdayIndex;
      const weekday = match?.[2] as Weekday;
      if (!WEEKDAY_INDEXES.includes(index) || !WEEKDAYS.includes(weekday)) return null;
      value.monthlyType = "WEEKDAYOFMONTH";
      value.weekdayIndex = index;
      value.weekday = weekday;
    } else {
      return null;
    }
  }

  for (const line of lines.slice(1)) {
    const match = /^(EXDATE|RDATE):(.+)$/.exec(line);
    const values = match ? dates(match[2]) : null;
    if (!match || !values) return null;
    if (match[1] === "EXDATE") value.exdates = values;
    else value.rdates = values;
  }

  return value;
}

/**
 * The value of a stored rule, or `null` when the rule is not exactly one the editor
 * writes back unchanged (the caller then keeps the raw rule).
 */
export function parse(rule: string): RecurrenceValue | null {
  const normalized = rule.replace(/\r\n/g, "\n").trim();
  const value = parseLoose(normalized);
  return value && serialize(value) === normalized ? value : null;
}

type Translate = (key: string, named?: Record<string, unknown>) => string;

export function weekdayName(day: Weekday, locale: string): string {
  // 2024-01-07 is a Sunday.
  const date = new Date(2024, 0, 7 + WEEKDAYS.indexOf(day));
  return new Intl.DateTimeFormat(locale, { weekday: "long" }).format(date);
}

export function monthName(month: number, locale: string): string {
  return new Intl.DateTimeFormat(locale, { month: "long" }).format(new Date(2024, month - 1, 1));
}

export function formatDate(date: string, locale: string): string {
  const [year, month, day] = date.split("-").map(Number);
  return new Intl.DateTimeFormat(locale, { dateStyle: "medium" }).format(
    new Date(year, month - 1, day),
  );
}

export function weekdayIndexLabel(index: WeekdayIndex, t: Translate): string {
  return {
    "+1": t("first"),
    "+2": t("second"),
    "+3": t("third"),
    "+4": t("fourth"),
    "-1": t("last"),
  }[index];
}

/** A one-line summary of the rule, e.g. "Every 1 week(s) on Monday, Wednesday, 6 times". */
export function describe(value: RecurrenceValue, t: Translate, locale: string): string {
  const interval = { interval: value.interval };
  const parts = [
    {
      DAILY: () => t("Every %(interval)s day(s)", interval),
      WEEKLY: () => t("Every %(interval)s week(s)", interval),
      MONTHLY: () => t("Every %(interval)s month(s)", interval),
      YEARLY: () => t("Every %(interval)s year(s)", interval),
    }[value.freq](),
  ];

  if (value.freq === "WEEKLY" && value.weekdays.length) {
    const weekdays = WEEKDAYS.filter((day) => value.weekdays.includes(day))
      .map((day) => weekdayName(day, locale))
      .join(", ");
    parts.push(t("on %(weekdays)s", { weekdays }));
  }

  if (value.freq === "MONTHLY" && value.monthlyType === "DAYOFMONTH") {
    parts.push(t("on day %(day)s", { day: value.monthDay }));
  }

  if (value.freq === "YEARLY" && value.monthlyType === "DAYOFMONTH") {
    parts.push(
      t("on %(day)s %(month)s", { day: value.monthDay, month: monthName(value.month, locale) }),
    );
  }

  if (value.monthlyType === "WEEKDAYOFMONTH" && value.freq !== "WEEKLY" && value.freq !== "DAILY") {
    const named = {
      index: weekdayIndexLabel(value.weekdayIndex, t),
      weekday: weekdayName(value.weekday, locale),
      month: monthName(value.month, locale),
    };
    parts.push(
      value.freq === "MONTHLY"
        ? t("on the %(index)s %(weekday)s", named)
        : t("on the %(index)s %(weekday)s of %(month)s", named),
    );
  }

  if (value.end.type === "count") {
    parts.push(t("ends after %(count)s occurrence(s)", { count: value.end.count }));
  }
  if (value.end.type === "until") {
    parts.push(t("until %(date)s", { date: formatDate(value.end.until, locale) }));
  }

  const list = (values: string[]) =>
    values.map((item) => formatDate(fromDateTime(item), locale)).join("; ");
  if (value.rdates.length) parts.push(t("including %(dates)s", { dates: list(value.rdates) }));
  if (value.exdates.length) parts.push(t("except %(dates)s", { dates: list(value.exdates) }));

  return parts.join(", ");
}
