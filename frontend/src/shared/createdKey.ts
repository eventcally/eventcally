/**
 * Takes the secret a create page handed over through the history state (`router.push({ state:
 * { key } })`) and removes it from the entry. Browsers keep `history.state` across a reload
 * and back/forward, so without removing it the key would show again.
 */
export function takeCreatedKey(): string | null {
  const state = history.state as Record<string, unknown> | null;
  const key = typeof state?.key === "string" ? state.key : null;
  if (key !== null) {
    const { key: _removed, ...rest } = state as Record<string, unknown>;
    history.replaceState(rest, "");
  }
  return key;
}
