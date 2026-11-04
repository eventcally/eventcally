import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import ReadProps from "./ReadProps.vue";

describe("ReadProps", () => {
  it("shows values, links and lists and hides empty optional rows", () => {
    const wrapper = mount(ReadProps, {
      props: {
        rows: [
          { label: "Name", value: "Jam" },
          { label: "Event", value: "Jam Session", href: "/event/4" },
          { label: "Roles", list: ["admin", "event_verifier"] },
          { label: "Reason", value: "", hideWhenEmpty: true },
          { label: "Rating", value: null },
          { label: "Link", value: "", href: "/x" },
        ],
      },
    });

    const labels = wrapper.findAll("dt").map((d) => d.text());
    expect(labels).toEqual(["Name", "Event", "Roles", "Rating", "Link"]);
    expect(wrapper.find("a").attributes("href")).toBe("/event/4");
    expect(wrapper.findAll("li").map((l) => l.text())).toEqual(["admin", "event_verifier"]);
    expect(wrapper.findAll("a")).toHaveLength(1);
  });
});
