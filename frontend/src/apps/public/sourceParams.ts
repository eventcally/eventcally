export const SOURCE_PARAMS = [
  "src",
  "utm_source",
  "utm_medium",
  "utm_campaign",
];

/** Removes the visit-source parameters from the address bar (the server already logged them). */
export function stripSourceParams(
  loc: Location = window.location,
  hist: History = window.history,
): void {
  try {
    const url = new URL(loc.href);
    let removed = false;
    for (const name of SOURCE_PARAMS) {
      if (url.searchParams.has(name)) {
        url.searchParams.delete(name);
        removed = true;
      }
    }
    if (removed) {
      hist.replaceState(hist.state, "", url.pathname + url.search + url.hash);
    }
  } catch {
    // never block the boot
  }
}
