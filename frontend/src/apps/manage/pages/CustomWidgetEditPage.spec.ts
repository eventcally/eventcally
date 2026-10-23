import { flushPromises, mount } from "@vue/test-utils";
import { createBootstrap } from "bootstrap-vue-next";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createI18n } from "vue-i18n";

vi.mock("@/shared/boot", () => ({ boot: { locale: "en", csrfToken: "x", loginUrl: "/login" } }));

const GET = vi.fn();
const POST = vi.fn();
const PUT = vi.fn();
vi.mock("@/shared/api", () => ({
  api: {
    GET: (...a: unknown[]) => GET(...a),
    POST: (...a: unknown[]) => POST(...a),
    PUT: (...a: unknown[]) => PUT(...a),
  },
}));

// The iframe and iframeResizer are covered by the preview's own spec.
vi.mock("../components/CustomWidgetPreview.vue", async () => {
  const { defineComponent, h } = await import("vue");
  return {
    default: defineComponent({
      props: ["type", "settings", "size"],
      setup: (props) => () =>
        h("div", { class: "preview-stub", "data-type": props.type, "data-size": props.size }),
    }),
  };
});

import { takeFlash } from "../flash";
import CustomWidgetEditPage from "./CustomWidgetEditPage.vue";

const assign = vi.fn();

function mountPage(props: { organizationId: number; id?: number } = { organizationId: 3 }) {
  return mount(CustomWidgetEditPage, {
    props,
    attachTo: document.body,
    global: {
      plugins: [
        createBootstrap(),
        createI18n({ legacy: false, locale: "en", messages: { en: {} } }),
      ],
    },
  });
}

describe("CustomWidgetEditPage", () => {
  beforeEach(() => {
    [GET, POST, PUT, assign].forEach((f) => f.mockReset());
    vi.stubGlobal("location", { origin: "http://localhost", assign });
    sessionStorage.clear();
  });

  it("creates a widget with the defaults of the organization", async () => {
    POST.mockResolvedValue({ data: { id: 9 } });
    const wrapper = mountPage();
    await flushPromises();

    expect(GET).not.toHaveBeenCalled();
    expect(wrapper.find(".preview-stub").attributes("data-type")).toBe("search");

    await wrapper.find('[data-test="widget-name"]').setValue("Neues Widget");
    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(POST).toHaveBeenCalledWith("/bff/manage/organizations/{id}/custom-widgets", {
      params: { path: { id: 3 } },
      body: {
        widget_type: "search",
        name: "Neues Widget",
        settings: expect.objectContaining({ organizationId: 3, layout: "card", eventsPerPage: 10 }),
      },
    });
    expect(assign).toHaveBeenCalledWith("/manage/admin_unit/3/custom-widgets");
    expect(takeFlash()).toBe("Widget successfully saved");
  });

  it("keeps the settings of each type while switching", async () => {
    PUT.mockResolvedValue({});
    const wrapper = mountPage();
    await flushPromises();

    await wrapper.find("#field-eventsPerPage").setValue("25");
    await wrapper.find('[data-test="widget-type"]').setValue("calendar");
    await flushPromises();
    expect(wrapper.find(".preview-stub").attributes("data-type")).toBe("calendar");
    expect(wrapper.find("#field-calendarType").exists()).toBe(true);

    await wrapper.find('[data-test="widget-type"]').setValue("search");
    await flushPromises();
    expect((wrapper.find("#field-eventsPerPage").element as HTMLInputElement).value).toBe("25");
  });

  it("loads a widget for the update and sends a PUT", async () => {
    GET.mockResolvedValue({
      data: {
        id: 8,
        organization_id: 3,
        widget_type: "calendar",
        name: "Kalender",
        settings: { calendarType: "month", legacyKey: "x" },
      },
    });
    PUT.mockResolvedValue({});
    const wrapper = mountPage({ organizationId: 3, id: 8 });
    await flushPromises();

    expect(GET).toHaveBeenCalledWith("/bff/manage/custom-widgets/{id}", {
      params: { path: { id: 8 } },
    });
    expect((wrapper.find('[data-test="widget-name"]').element as HTMLInputElement).value).toBe(
      "Kalender",
    );
    expect(wrapper.find(".preview-stub").attributes("data-type")).toBe("calendar");

    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(PUT).toHaveBeenCalledWith("/bff/manage/custom-widgets/{id}", {
      params: { path: { id: 8 } },
      body: {
        widget_type: "calendar",
        name: "Kalender",
        settings: expect.objectContaining({
          calendarType: "month",
          iFrameHeight: 600,
          legacyKey: "x",
          organizationId: 3,
        }),
      },
    });
    expect(assign).toHaveBeenCalledWith("/manage/admin_unit/3/custom-widgets");
  });

  it("shows a name error inline and stays", async () => {
    POST.mockResolvedValue({
      error: { name: "Unprocessable", message: "x", errors: [{ loc: ["name"], msg: "Too short" }] },
    });
    const wrapper = mountPage();
    await flushPromises();

    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(wrapper.text()).toContain("Too short");
    expect(assign).not.toHaveBeenCalled();
  });

  it("shows other errors as an alert", async () => {
    POST.mockResolvedValue({ error: { name: "Forbidden", message: "Not allowed" } });
    const wrapper = mountPage();
    await flushPromises();

    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(wrapper.find(".alert-danger").text()).toBe("Not allowed");
    expect(assign).not.toHaveBeenCalled();
  });

  it("goes back to the list on cancel", async () => {
    const wrapper = mountPage();
    await flushPromises();

    expect(wrapper.find('a[href="/manage/admin_unit/3/custom-widgets"]').text()).toBe("Cancel");
  });

  it("switches the preview size", async () => {
    const wrapper = mountPage();
    await flushPromises();

    await wrapper.findAll("input[type=radio]")[1].setValue(true);

    expect(wrapper.find(".preview-stub").attributes("data-size")).toBe("768px");
  });
});
