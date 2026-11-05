import { flushPromises } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/shared/boot", () => ({ boot: { base: "/", locale: "en", csrfToken: "x" } }));

const GET = vi.fn();
vi.mock("@/shared/api", () => ({ api: { GET: (...a: unknown[]) => GET(...a) } }));

import { mountPage } from "../testing";
import WebhookDeliveriesPage from "./WebhookDeliveriesPage.vue";

const URL = "/manage/admin_unit/3/app/5/webhook_deliveries";
const LIST = "/bff/manage/organizations/{id}/apps/{app_id}/webhook-deliveries";
const row = (over = {}) => ({
  id: 7,
  event_type: "app.installed",
  timestamp: "2026-11-04T10:00:00Z",
  organization: "Meine Crew",
  ...over,
});
const page = (items: object[]) => ({
  data: {
    items,
    page: 1,
    per_page: 20,
    total: items.length,
    pages: 1,
    can_write: false,
    app_title: "Meine App",
  },
});

describe("WebhookDeliveriesPage", () => {
  beforeEach(() => {
    GET.mockReset();
    document.body.innerHTML = "";
  });

  it("lists the deliveries with a link to each", async () => {
    GET.mockResolvedValue(page([row()]));
    const { wrapper } = await mountPage(
      WebhookDeliveriesPage,
      { organizationId: 3, appId: 5 },
      URL,
    );

    expect(GET).toHaveBeenCalledWith(LIST, {
      params: { path: { id: 3, app_id: 5 }, query: { page: 1 } },
    });
    expect(wrapper.find(".breadcrumb").text()).toContain("Meine App");
    expect(wrapper.find(".breadcrumb").text()).toContain("Webhook deliveries");
    expect(wrapper.find("table").text()).toContain("app.installed");
    expect(wrapper.find("table").text()).toContain("Meine Crew");

    await wrapper.find(".row-actions button").trigger("click");
    await flushPromises();
    expect(document.querySelector(".dropdown-item")?.getAttribute("href")).toBe(
      "/manage/admin_unit/3/app/5/webhook_delivery/7",
    );
  });

  it("shows no table for an empty list and the error of a failed load", async () => {
    GET.mockResolvedValue(page([]));
    const empty = await mountPage(WebhookDeliveriesPage, { organizationId: 3, appId: 5 }, URL);
    expect(empty.wrapper.find("table").exists()).toBe(false);

    GET.mockResolvedValue({ error: { message: "Forbidden" } });
    const failed = await mountPage(WebhookDeliveriesPage, { organizationId: 3, appId: 5 }, URL);
    expect(failed.wrapper.find(".alert-danger").text()).toBe("Forbidden");
  });
});
