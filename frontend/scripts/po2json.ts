import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { po } from "gettext-parser";

const here = dirname(fileURLToPath(import.meta.url));
const root = resolve(here, "../..");
const out = resolve(here, "../src/locales");

/** Convert a gettext message to vue-i18n message syntax. */
export function toVueI18n(text: string): string {
  const placeholders: string[] = [];
  const withTokens = text.replace(/%\((\w+)\)[sd]/g, (_m, name: string) => {
    placeholders.push(name);
    return `\u0000${placeholders.length - 1}\u0000`;
  });
  const escaped = withTokens.replace(/[{}@$|]/g, (c) => `{'${c}'}`);
  return escaped.replace(/\u0000(\d+)\u0000/g, (_m, i: string) => `{${placeholders[Number(i)]}}`);
}

export function poToMessages(content: Buffer | string): Record<string, string> {
  const parsed = po.parse(content);
  const messages: Record<string, string> = {};
  for (const entries of Object.values(parsed.translations)) {
    for (const [msgid, entry] of Object.entries(entries)) {
      const msgstr = entry.msgstr?.[0];
      if (!msgid) continue;
      if (entry.comments?.flag?.includes("fuzzy")) continue;
      if (msgstr) {
        messages[msgid] = toVueI18n(msgstr);
      } else if (/%\(\w+\)[sd]/.test(msgid)) {
        // Untranslated (e.g. English): the msgid is the text, but its gettext placeholders
        // still have to become vue-i18n ones.
        messages[msgid] = toVueI18n(msgid);
      }
    }
  }
  return messages;
}

function main() {
  mkdirSync(out, { recursive: true });
  for (const locale of ["de", "en"]) {
    const file = resolve(root, `project/translations/${locale}/LC_MESSAGES/messages.po`);
    const messages = poToMessages(readFileSync(file));
    writeFileSync(resolve(out, `${locale}.json`), JSON.stringify(messages, null, 2) + "\n");
  }
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main();
}
