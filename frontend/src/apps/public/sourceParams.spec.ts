import { describe, expect, it, vi } from "vitest";
import { stripSourceParams } from "./sourceParams";

function run(href: string) {
  const replaceState = vi.fn();
  stripSourceParams(
    { href } as Location,
    { state: { a: 1 }, replaceState } as unknown as History,
  );
  return replaceState;
}

describe("stripSourceParams", () => {
  it("removes the four params and keeps others and the hash", () => {
    const fn = run(
      "https://x.test/event/1?src=a&utm_source=b&utm_medium=c&utm_campaign=d&page=2#top",
    );
    expect(fn).toHaveBeenCalledWith({ a: 1 }, "", "/event/1?page=2#top");
  });

  it("does not touch the history without source params", () => {
    expect(run("https://x.test/event/1?page=2")).not.toHaveBeenCalled();
  });

  it("never throws", () => {
    expect(() => stripSourceParams({ href: "nope" } as Location)).not.toThrow();
  });
});
