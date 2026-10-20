import { createI18n } from "vue-i18n";
import de from "@/locales/de.json";
import en from "@/locales/en.json";

function readLocale(): string {
  try {
    const el = document.getElementById("boot");
    return el?.textContent ? JSON.parse(el.textContent).locale : "en";
  } catch {
    return "en";
  }
}

// The msgid is the key, so a missing translation falls back to the English text.
export const i18n = createI18n({
  legacy: false,
  locale: readLocale(),
  fallbackLocale: "en",
  messages: { de, en },
  missingWarn: false,
  fallbackWarn: false,
});
