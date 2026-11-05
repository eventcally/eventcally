import { flushPromises } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/shared/boot", () => ({ boot: { base: "/", locale: "en", csrfToken: "x" } }));

const GET = vi.fn();
const POST = vi.fn();
vi.mock("@/shared/api", () => ({
  api: { GET: (...a: unknown[]) => GET(...a), POST: (...a: unknown[]) => POST(...a) },
}));
const success = vi.hoisted(() => vi.fn());
const failure = vi.hoisted(() => vi.fn());
vi.mock("@/shared/notify", () => ({ useNotify: () => ({ success, error: failure }) }));

import { mountPage } from "../testing";
import WebhookDeliveryPage from "./WebhookDeliveryPage.vue";

const URL = "/manage/admin_unit/3/app/5/webhook_delivery/7";
const READ = "/bff/manage/organizations/{id}/apps/{app_id}/webhook-deliveries/{delivery_id}";
const ATTEMPTS = `${READ}/attempts`;
const delivery = (over = {}) => ({
  id: 7,
  event_type: "app.installed",
  timestamp: "2026-11-04T10:00:00Z",
  organization: "Meine Crew",
  app_id: 5,
  app_title: "Meine App",
  can_attempt: true,
  ...over,
});
const attempt = (over = {}) => ({
  id: 2,
  start_at: "2026-11-04T10:00:00Z",
  end_at: "2026-11-04T10:00:01Z",
  url: "https://hook.example",
  status: "ok",
  status_code: "200",
  ...over,
});
const attempts = (items: object[]) => ({
  data: { items, page: 1, per_page: 20, total: items.length, pages: 1, can_write: true },
});
const stub = (d: object, a: object) =>
  GET.mockImplementation(async (url: string) => (url === READ ? d : a));
const mountIt = () =>
  mountPage(WebhookDeliveryPage, { organizationId: 3, appId: 5, id: 7 }, URL);

describe("WebhookDeliveryPage", () => {
  beforeEach(() => {
    [GET, POST, success, failure].forEach((f) => f.mockReset());
    document.body.innerHTML = "";
  });

  it("shows the delivery and its attempts", async () => {
    stub({ data: delivery() }, attempts([attempt()]));
    const { wrapper } = await mountIt();

    const path = { id: 3, app_id: 5, delivery_id: 7 };
    expect(GET).toHaveBeenCalledWith(READ, { params: { path } });
    expect(GET).toHaveBeenCalledWith(ATTEMPTS, { params: { path, query: { page: 1 } } });
    expect(wrapper.find(".breadcrumb").text()).toContain("Meine App");
    expect(wrapper.find(".breadcrumb").text()).toContain("Webhook delivery 7");
    expect(wrapper.text()).toContain("app.installed");
    expect(wrapper.text()).toContain("Meine Crew");
    expect(wrapper.find("[data-test=attempts] table").text()).toContain("200");
    expect(wrapper.find("[data-test=attempts] table").text()).toContain("https://hook.example");
  });

  it("delivers again and reloads the attempts", async () => {
    stub({ data: delivery() }, attempts([]));
    POST.mockResolvedValue({ data: { message: "Created" } });
    const { wrapper } = await mountIt();

    await wrapper.find("[data-test=deliver-again]").trigger("click");
    await flushPromises();

    expect(POST).toHaveBeenCalledWith(ATTEMPTS, {
      params: { path: { id: 3, app_id: 5, delivery_id: 7 } },
    });
    expect(success).toHaveBeenCalledWith("Created");
    expect(GET.mock.calls.filter((c) => c[0] === ATTEMPTS)).toHaveLength(2);
  });

  it("toasts the error of a failed attempt", async () => {
    stub({ data: delivery() }, attempts([]));
    POST.mockResolvedValue({ error: { message: "Nope" } });
    const { wrapper } = await mountIt();

    await wrapper.find("[data-test=deliver-again]").trigger("click");
    await flushPromises();

    expect(failure).toHaveBeenCalledWith("Nope");
  });

  it("offers no new attempt without permission", async () => {
    stub({ data: delivery({ can_attempt: false }) }, attempts([attempt()]));
    const { wrapper } = await mountIt();

    expect(wrapper.find("[data-test=deliver-again]").exists()).toBe(false);
  });

  it("shows the errors of failed loads", async () => {
    stub({ error: { message: "Not found" } }, { error: { message: "No attempts" } });
    const { wrapper } = await mountIt();

    const alerts = wrapper.findAll(".alert-danger").map((a) => a.text());
    expect(alerts).toEqual(["Not found"]);

    stub({ data: delivery() }, { error: { message: "No attempts" } });
    const second = await mountIt();
    expect(second.wrapper.find("[data-test=attempts] .alert-danger").text()).toBe("No attempts");
  });
});
