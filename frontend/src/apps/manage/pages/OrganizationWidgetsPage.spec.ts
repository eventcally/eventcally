import { flushPromises } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/shared/boot", () => ({ boot: { base: "/", locale: "en", csrfToken: "x" } }));

const GET = vi.fn();
const PUT = vi.fn();
vi.mock("@/shared/api", () => ({
  api: { GET: (...a: unknown[]) => GET(...a), PUT: (...a: unknown[]) => PUT(...a) },
}));
const success = vi.hoisted(() => vi.fn());
vi.mock("@/shared/notify", () => ({ useNotify: () => ({ success, error: vi.fn() }) }));

import { mountPage } from "../testing";
import OrganizationWidgetsPage from "./OrganizationWidgetsPage.vue";

const URL = "/manage/admin_unit/3/widgets";
const PATH = "/bff/manage/organizations/{id}/widget-settings";
const settings = (over = {}) => ({
  data: {
    id: 3,
    font: "Arial",
    background_color: "#ffffff",
    primary_color: "#007bff",
    link_color: "#007bff",
    loader_url: "http://localhost/static/widget-loader.js",
    iframe_url: "http://localhost/organizations/3/widget/eventdates",
    preview_url: "/organizations/3/widget/eventdates",
    ...over,
  },
});

describe("OrganizationWidgetsPage", () => {
  beforeEach(() => {
    [GET, PUT, success].forEach((f) => f.mockReset());
    GET.mockResolvedValue(settings());
  });

  it("loads the colors and saves them", async () => {
    PUT.mockResolvedValue({ data: { message: "Settings successfully updated" } });
    const { wrapper } = await mountPage(OrganizationWidgetsPage, { organizationId: 3 }, URL);

    expect(GET).toHaveBeenCalledWith(PATH, { params: { path: { id: 3 } } });
    expect(wrapper.find(".breadcrumb").text()).toContain("Widgets");
    expect((wrapper.find("#widget_font").element as HTMLInputElement).value).toBe("Arial");
    expect((wrapper.find("#widget_primary_color").element as HTMLInputElement).value).toBe(
      "#007bff",
    );

    await wrapper.find("#widget_background_color").setValue("#eceef0");
    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(PUT).toHaveBeenCalledWith(PATH, {
      params: { path: { id: 3 } },
      body: {
        font: "Arial",
        background_color: "#eceef0",
        primary_color: "#007bff",
        link_color: "#007bff",
      },
    });
    expect(success).toHaveBeenCalledWith("Settings successfully updated");
  });

  it("shows field errors and other errors", async () => {
    PUT.mockResolvedValueOnce({
      error: { errors: [{ loc: ["font"], msg: "Too long" }, { loc: ["x"], msg: "Other" }] },
    });
    const { wrapper } = await mountPage(OrganizationWidgetsPage, { organizationId: 3 }, URL);
    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(wrapper.find("#widget_font").classes()).toContain("is-invalid");
    expect(wrapper.find(".invalid-feedback").text()).toBe("Too long");
    expect(wrapper.find(".alert-danger").text()).toBe("Other");

    PUT.mockResolvedValueOnce({ error: { message: "Kaputt" } });
    await wrapper.find("form").trigger("submit");
    await flushPromises();
    expect(wrapper.find(".alert-danger").text()).toBe("Kaputt");
    expect(success).not.toHaveBeenCalled();
  });

  it("shows the error of the load", async () => {
    GET.mockResolvedValue({ error: { message: "Forbidden" } });
    const { wrapper } = await mountPage(OrganizationWidgetsPage, { organizationId: 3 }, URL);

    expect(wrapper.find(".alert-danger").text()).toBe("Forbidden");
    expect(wrapper.find("form").exists()).toBe(false);
  });

  it("opens the embed instructions and links the preview", async () => {
    const { wrapper } = await mountPage(OrganizationWidgetsPage, { organizationId: 3 }, URL);

    expect(wrapper.find('a[href="/organizations/3/widget/eventdates"]').text()).toContain(
      "Preview",
    );
    await wrapper.find('[data-test="embed"]').trigger("click");
    await flushPromises();

    const head = document.body.querySelector<HTMLTextAreaElement>('[data-test="head-snippet"]');
    expect(head?.value).toContain("http://localhost/static/widget-loader.js");
    expect(
      document.body.querySelector<HTMLTextAreaElement>('[data-test="body-snippet"]')?.value,
    ).toContain('data-widget-organization-id="3"');
    expect(
      document.body.querySelector<HTMLTextAreaElement>('[data-test="iframe-snippet"]')?.value,
    ).toBe('<iframe src="http://localhost/organizations/3/widget/eventdates"></iframe>');
  });
});
