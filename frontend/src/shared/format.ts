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
