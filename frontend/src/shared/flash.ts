// A success message that has to survive a full page load (the editor and the list are
// separate page loads, because the editor runs without navbar and footer).
const KEY = "eventcally.flash";

export function setFlash(message: string): void {
  try {
    sessionStorage.setItem(KEY, message);
  } catch {
    // storage blocked: no message, the redirect still works
  }
}

export function takeFlash(): string | null {
  try {
    const message = sessionStorage.getItem(KEY);
    sessionStorage.removeItem(KEY);
    return message;
  } catch {
    return null;
  }
}
