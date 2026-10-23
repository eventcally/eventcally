import { describe, expect, it } from "vitest";
import { toFieldErrors } from "./fieldErrors";

describe("toFieldErrors", () => {
  it("keys known errors by their dotted location", () => {
    const { byKey, unmatched } = toFieldErrors(
      [
        { loc: ["name"], msg: "Taken" },
        { loc: ["location", "city"], msg: "Required" },
      ],
      ["name", "location.city"],
    );
    expect(byKey).toEqual({ name: "Taken", "location.city": "Required" });
    expect(unmatched).toEqual([]);
  });

  it("keeps the first error of a field and collects unknown locations", () => {
    const { byKey, unmatched } = toFieldErrors(
      [
        { loc: ["name"], msg: "First" },
        { loc: ["name"], msg: "Second" },
        { loc: ["other"], msg: "Unknown" },
      ],
      ["name"],
    );
    expect(byKey).toEqual({ name: "First" });
    expect(unmatched).toEqual(["Unknown"]);
  });
});
