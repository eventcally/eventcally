import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import ManageBreadcrumb from "./ManageBreadcrumb.vue";

describe("ManageBreadcrumb", () => {
  it("shows the items, the last one as the current page", () => {
    const wrapper = mount(ManageBreadcrumb, {
      props: {
        organizationId: 3,
        items: [{ label: "Places", href: "/places" }, { label: "Delete" }],
      },
    });

    expect(wrapper.findAll("li")).toHaveLength(2);
    expect(wrapper.find("a").attributes("href")).toBe("/places");
    expect(wrapper.find("li.active").text()).toBe("Delete");
  });

  it("puts the organization first when its name is given", () => {
    const wrapper = mount(ManageBreadcrumb, {
      props: { organizationId: 3, organizationName: "Meine Crew", items: [{ label: "Places" }] },
    });

    expect(wrapper.find("a").attributes("href")).toBe("/manage/admin_unit/3");
    expect(wrapper.find("a").text()).toBe("Meine Crew");
    expect(wrapper.findAll("li")).toHaveLength(2);
  });
});
