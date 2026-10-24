// Suggests a short name for an organization name: lowercase, umlauts transliterated,
// only word characters kept (always valid for the server's `^\w+$`).
export function suggestShortName(name: string): string {
  const transliterated = name
    .toLowerCase()
    .replace(/ä/g, "ae")
    .replace(/ö/g, "oe")
    .replace(/ü/g, "ue")
    .replace(/ß/g, "ss");
  return (transliterated.match(/\w/g) ?? []).join("");
}
