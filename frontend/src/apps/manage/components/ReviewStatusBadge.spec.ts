import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import ReviewStatusBadge from "./ReviewStatusBadge.vue";

describe("ReviewStatusBadge", () => {
  it.each([
    [1, "text-bg-info"],
    [2, "text-bg-success"],
    [3, "text-bg-danger"],
    [9, "text-bg-secondary"],
  ])("colors status %i", (status, expected) => {
    const wrapper = mount(ReviewStatusBadge, { props: { status, label: "Label" } });

    expect(wrapper.text()).toBe("Label");
    expect(wrapper.classes()).toContain(expected);
  });
});
