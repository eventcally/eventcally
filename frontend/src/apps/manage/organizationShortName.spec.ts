import { describe, expect, it } from "vitest";
import { suggestShortName } from "./organizationShortName";

describe("suggestShortName", () => {
  it("lowercases and drops spaces and punctuation", () => {
    expect(suggestShortName("Meine Neue Crew!")).toBe("meineneuecrew");
  });

  it("transliterates umlauts and sharp s", () => {
    expect(suggestShortName("Zürich Größe Bühne Äpfel")).toBe("zuerichgroessebuehneaepfel");
  });

  it("keeps digits and underscores", () => {
    expect(suggestShortName("Crew_2 / 3")).toBe("crew_23");
  });

  it("returns an empty string for an empty name", () => {
    expect(suggestShortName("")).toBe("");
    expect(suggestShortName(" !? ")).toBe("");
  });
});
