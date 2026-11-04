import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import { createI18n } from "vue-i18n";
import ManageBreadcrumb from "./ManageBreadcrumb.vue";

const i18n = createI18n({ legacy: false, locale: "en", messages: { en: { Docs: "Docs" } } });

describe("ManageBreadcrumb", () => {
  it("shows the items, the last one as the current page", () => {
    const wrapper = mount(ManageBreadcrumb, {
      props: {
        organizationId: 3,
        items: [{ label: "Places", href: "/places" }, { label: "Delete" }],
      },
      global: { plugins: [i18n] },
    });

    expect(wrapper.findAll("li")).toHaveLength(2);
    expect(wrapper.find("a").attributes("href")).toBe("/places");
    expect(wrapper.find("li.active").text()).toBe("Delete");
  });

  it("puts the organization first when its name is given", () => {
    const wrapper = mount(ManageBreadcrumb, {
      props: { organizationId: 3, organizationName: "Meine Crew", items: [{ label: "Places" }] },
      global: { plugins: [i18n] },
    });

    expect(wrapper.find("a").attributes("href")).toBe("/manage/admin_unit/3");
    expect(wrapper.find("a").text()).toBe("Meine Crew");
    expect(wrapper.findAll("li")).toHaveLength(2);
  });

  it("shows the docs button on the right when a docs url is given", () => {
    const wrapper = mount(ManageBreadcrumb, {
      props: { organizationId: 3, docsUrl: "https://docs.test/x", items: [{ label: "Places" }] },
      global: { plugins: [i18n] },
    });

    const docs = wrapper.find("a.btn");
    expect(docs.attributes("href")).toBe("https://docs.test/x");
    expect(docs.text()).toBe("Docs");
    expect(wrapper.findAll("li.breadcrumb-item")).toHaveLength(1);
  });
});
