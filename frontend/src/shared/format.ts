export function formatDateTime(iso: string | null | undefined, locale: string): string {
  if (!iso) return "";
  return new Intl.DateTimeFormat(locale, { dateStyle: "medium", timeStyle: "short" }).format(
    new Date(iso),
  );
}

export function formatDate(iso: string | null | undefined, locale: string): string {
  if (!iso) return "";
  return new Intl.DateTimeFormat(locale, { dateStyle: "medium" }).format(new Date(iso));
}

/** Mirrors the `render_event_date` macro: full date, time unless all-day, end only if it adds information. */
export function formatEventDate(
  start: string,
  end: string | null | undefined,
  allday: boolean,
  locale: string,
): string {
  const date = new Intl.DateTimeFormat(locale, { dateStyle: "full" });
  const time = new Intl.DateTimeFormat(locale, { timeStyle: "short" });
  const startDate = date.format(new Date(start));
  let result = startDate;
  if (!allday) result += ` ${time.format(new Date(start))}`;

  if (end) {
    const endDate = date.format(new Date(end));
    const differs = endDate !== startDate;
    if (differs || !allday) result += " - ";
    if (differs) result += endDate;
    if (!allday) result += `${differs ? " " : ""}${time.format(new Date(end))}`;
  }
  return result;
}

/** Short date, plus the short time unless the event is all-day (the manage list's start column). */
export function formatStart(iso: string | null | undefined, allday: boolean, locale: string): string {
  if (!iso) return "";
  const date = new Date(iso);
  const day = new Intl.DateTimeFormat(locale, { dateStyle: "short" }).format(date);
  if (allday) return day;
  // Joined by a space: a combined date-time format would put a comma between them.
  return `${day} ${new Intl.DateTimeFormat(locale, { timeStyle: "short" }).format(date)}`;
}

const FILE_SIZE_UNITS = ["KB", "MB", "GB", "TB", "PB", "EB", "ZB"];

/** Same output as the Jinja filter `human_file_size`: whole units, shifted by 1024. */
export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} bytes`;
  let value = Math.floor(bytes / 1024);
  let unit = 0;
  while (value >= 1024 && unit < FILE_SIZE_UNITS.length - 1) {
    value = Math.floor(value / 1024);
    unit++;
  }
  return `${value}${FILE_SIZE_UNITS[unit]}`;
}
