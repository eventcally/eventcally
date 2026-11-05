import { beforeEach, describe, expect, it } from "vitest";
import { takeCreatedKey } from "./createdKey";

describe("takeCreatedKey", () => {
  beforeEach(() => history.replaceState(null, ""));

  it("returns the key once and keeps the other state", () => {
    history.replaceState({ key: "secret", position: 3 }, "");

    expect(takeCreatedKey()).toBe("secret");
    expect(history.state).toEqual({ position: 3 });
    expect(takeCreatedKey()).toBeNull();
  });

  it("returns null without a state or a string key", () => {
    expect(takeCreatedKey()).toBeNull();
    history.replaceState({ key: 5 }, "");
    expect(takeCreatedKey()).toBeNull();
    expect(history.state).toEqual({ key: 5 });
  });
});
