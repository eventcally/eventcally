export type LinkifyPart = { text: string } | { href: string; text: string };

// `http(s)://…` and `www.…` up to the next whitespace. Bare domains and e-mail addresses
// stay text, and so does anything else (`javascript:`), because only these two start a link.
const URL_PATTERN = /(?<![\w.@/-])(?:https?:\/\/|www\.)\S+/gi;
const TRAILING = new Set([".", ",", ";", ":", "!", "?", "'", '"']);

const count = (text: string, char: string) => text.split(char).length - 1;

/** Moves sentence punctuation and unbalanced closing brackets at the end out of the link. */
function trimUrl(url: string): [string, string] {
  let end = url.length;

  while (end > 0) {
    const last = url[end - 1];
    const head = url.slice(0, end);
    const closing = last === ")" ? "(" : last === "]" ? "[" : null;
    const unbalanced = closing !== null && count(head, last) > count(head, closing);

    if (!TRAILING.has(last) && !unbalanced) break;
    end--;
  }

  return [url.slice(0, end), url.slice(end)];
}

/** A port of Jinja's `urlize` for web addresses: the text split into plain and link parts. */
export function linkify(text: string): LinkifyPart[] {
  const parts: LinkifyPart[] = [];
  const pushText = (value: string) => {
    if (!value) return;
    const last = parts[parts.length - 1];
    if (last && !("href" in last)) last.text += value;
    else parts.push({ text: value });
  };

  let index = 0;

  for (const match of text.matchAll(URL_PATTERN)) {
    const [url, rest] = trimUrl(match[0]);
    pushText(text.slice(index, match.index));
    index = match.index + match[0].length;

    // A bare scheme or "www." without a host is not a link.
    if (/^(?:https?:\/\/|www\.)$/i.test(url)) {
      pushText(match[0]);
      continue;
    }

    parts.push({ href: /^www\./i.test(url) ? `https://${url}` : url, text: url });
    pushText(rest);
  }

  pushText(text.slice(index));
  return parts;
}
