import { describe, expect, it } from "vitest";
import { poToMessages, toVueI18n } from "./po2json";

describe("toVueI18n", () => {
  it("converts python placeholders", () => {
    expect(toVueI18n("%(count)d events of %(name)s")).toBe("{count} events of {name}");
  });

  it("escapes vue-i18n special characters", () => {
    expect(toVueI18n("a@b | {x} $")).toBe("a{'@'}b {'|'} {'{'}x{'}'} {'$'}");
  });
});

describe("poToMessages", () => {
  it("skips empty and fuzzy entries", () => {
    const po = [
      'msgid ""',
      'msgstr ""',
      '"Content-Type: text/plain; charset=UTF-8\\n"',
      "",
      'msgid "Users"',
      'msgstr "Benutzer"',
      "",
      '#, fuzzy',
      'msgid "Edit"',
      'msgstr "Bearbeiten?"',
      "",
      'msgid "Delete"',
      'msgstr ""',
    ].join("\n");

    expect(poToMessages(po)).toEqual({ Users: "Benutzer" });
  });

  it("uses the msgid with vue-i18n placeholders when a placeholder message is untranslated", () => {
    const po = ['msgid "%(n)d users"', 'msgstr ""', "", 'msgid "Plain"', 'msgstr ""'].join("\n");

    expect(poToMessages(po)).toEqual({ "%(n)d users": "{n} users" });
  });
});
