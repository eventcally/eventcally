import { describe, expect, it } from "vitest";
import { linkify } from "./linkify";

describe("linkify", () => {
  it("keeps plain text", () => {
    expect(linkify("Just text")).toEqual([{ text: "Just text" }]);
    expect(linkify("")).toEqual([]);
  });

  it("links http, https and www addresses", () => {
    expect(linkify("see http://a.de and https://b.de/x?y=1 or www.c.de")).toEqual([
      { text: "see " },
      { href: "http://a.de", text: "http://a.de" },
      { text: " and " },
      { href: "https://b.de/x?y=1", text: "https://b.de/x?y=1" },
      { text: " or " },
      { href: "https://www.c.de", text: "www.c.de" },
    ]);
  });

  it("keeps trailing punctuation outside the link", () => {
    expect(linkify("(see https://a.de/x), https://b.de.")).toEqual([
      { text: "(see " },
      { href: "https://a.de/x", text: "https://a.de/x" },
      { text: "), " },
      { href: "https://b.de", text: "https://b.de" },
      { text: "." },
    ]);
  });

  it("keeps balanced parentheses inside the link", () => {
    expect(linkify("https://de.wikipedia.org/wiki/Foo_(Bar)")).toEqual([
      { href: "https://de.wikipedia.org/wiki/Foo_(Bar)", text: "https://de.wikipedia.org/wiki/Foo_(Bar)" },
    ]);
    expect(linkify("(https://de.wikipedia.org/wiki/Foo_(Bar))")).toEqual([
      { text: "(" },
      { href: "https://de.wikipedia.org/wiki/Foo_(Bar)", text: "https://de.wikipedia.org/wiki/Foo_(Bar)" },
      { text: ")" },
    ]);
  });

  it("preserves newlines", () => {
    expect(linkify("a\nhttps://b.de\nc")).toEqual([
      { text: "a\n" },
      { href: "https://b.de", text: "https://b.de" },
      { text: "\nc" },
    ]);
  });

  it("never links other schemes, bare domains or e-mail addresses", () => {
    expect(linkify("javascript:alert(1) example.org a@b.de ftp://x.de")).toEqual([
      { text: "javascript:alert(1) example.org a@b.de ftp://x.de" },
    ]);
  });

  it("leaves a bare scheme as text", () => {
    expect(linkify("go to https:// now")).toEqual([{ text: "go to https:// now" }]);
  });
});
