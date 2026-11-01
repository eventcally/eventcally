// The query string of the iframe widget page `/organizations/<id>/widget/eventdates`. Customers
// embed that URL (and analytics counts the URLs that follow), so the shapes stay what the
// server-rendered page produced: a search is `?s_ft&s_bg&s_pr&s_li&date_from&date_to&category_id
// &keyword`, a page link is the current query plus `page`.

/** The style parameters `widget-loader.js` sends; the server turns them into the settings. */
const STYLE_KEYS = ["s_ft", "s_bg", "s_pr", "s_li"] as const;

/** What the filter form shows. A value the server would reject shows the defaults, as it did. */
export interface LegacyQuery {
  dateFrom: string;
  dateTo: string;
  categoryId: number;
  keyword: string;
  tag: string;
  page: number;
  perPage: number | null;
  /** The style parameters of the URL, kept for the next search. */
  styles: Record<(typeof STYLE_KEYS)[number], string>;
}

/** The date part (`YYYY-MM-DD`) of a value that may carry a time, or null when it is no date. */
export function dateOnly(value: string | null): string | null {
  if (!value) return null;
  const date = value.split(" ")[0].split("T")[0];
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(date);
  if (!match) return null;
  const parsed = new Date(Date.UTC(+match[1], +match[2] - 1, +match[3]));
  const valid =
    parsed.getUTCFullYear() === +match[1] &&
    parsed.getUTCMonth() === +match[2] - 1 &&
    parsed.getUTCDate() === +match[3];
  return valid ? date : null;
}

export function today(): string {
  return new Date().toLocaleDateString("sv"); // YYYY-MM-DD
}

function positiveInt(value: string | null): number | null {
  return value != null && /^\d+$/.test(value) && Number(value) > 0 ? Number(value) : null;
}

export function parseLegacyQuery(search: string): LegacyQuery {
  const params = new URLSearchParams(search);
  const styles = Object.fromEntries(
    STYLE_KEYS.map((k) => [k, params.get(k) ?? ""]),
  ) as LegacyQuery["styles"];
  const query: LegacyQuery = {
    dateFrom: today(),
    dateTo: "",
    categoryId: 0,
    keyword: "",
    tag: params.get("tag") ?? "",
    page: positiveInt(params.get("page")) ?? 1,
    perPage: positiveInt(params.get("per_page")),
    styles,
  };

  // All or nothing: one date the server cannot read and it ignores every filter.
  const from = params.has("date_from") ? params.get("date_from") : null;
  const to = params.get("date_to");
  const fromValid = from == null || from === "" || dateOnly(from) != null;
  const toValid = !to || dateOnly(to) != null;
  const categoryValid = !params.get("category_id") || /^\d+$/.test(params.get("category_id")!);
  if (!fromValid || !toValid || !categoryValid) {
    query.tag = "";
    return query;
  }

  if (from != null) query.dateFrom = dateOnly(from) ?? "";
  query.dateTo = dateOnly(to) ?? "";
  query.categoryId = Number(params.get("category_id") || 0);
  query.keyword = params.get("keyword") ?? "";
  return query;
}

/** The parameters of the BFF request: what the URL says, so the server decides what it means. */
export function apiParams(search: string): Record<string, string> {
  const params = new URLSearchParams(search);
  const result: Record<string, string> = {};
  for (const key of ["date_from", "date_to", "keyword", "category_id", "tag", "page", "per_page"]) {
    const value = params.get(key);
    if (value != null) result[key] = value;
  }
  return result;
}

export interface SearchForm {
  dateFrom: string;
  dateTo: string;
  categoryId: number;
  keyword: string;
}

/** The URL (path + query) of a search: the hidden style fields first, then the filter fields. */
export function searchUrl(
  pathname: string,
  form: SearchForm,
  query: Pick<LegacyQuery, "styles" | "tag" | "perPage">,
): string {
  const params = new URLSearchParams();
  for (const key of STYLE_KEYS) params.set(key, query.styles[key]);
  params.set("date_from", form.dateFrom);
  params.set("date_to", form.dateTo);
  params.set("category_id", String(form.categoryId));
  params.set("keyword", form.keyword);
  if (query.tag) params.set("tag", query.tag);
  if (query.perPage) params.set("per_page", String(query.perPage));
  return `${pathname}?${params}`;
}

/** The current query with `page` set (replaced in place, or appended). */
export function pageUrl(pathname: string, search: string, page: number): string {
  const params = new URLSearchParams(search);
  params.set("page", String(page));
  return `${pathname}?${params}`;
}
