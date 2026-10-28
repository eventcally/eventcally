import { enableAutoUnmount, flushPromises, mount } from "@vue/test-utils";
import { createBootstrap } from "bootstrap-vue-next";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { createI18n } from "vue-i18n";

vi.mock("@/shared/boot", () => ({ boot: { locale: "en", csrfToken: "x", loginUrl: "/login" } }));

const GET = vi.fn();
const POST = vi.fn();
vi.mock("@/shared/api", () => ({
  api: { GET: (...a: unknown[]) => GET(...a), POST: (...a: unknown[]) => POST(...a) },
}));

import EventReferenceRequestReviewPage from "./EventReferenceRequestReviewPage.vue";

const assign = vi.fn();
const BASE = "/bff/manage/organizations/{id}/incoming-event-reference-requests/{request_id}";
const PARAMS = { params: { path: { id: 3, request_id: 7 } } };

function review(overrides: Record<string, unknown> = {}) {
  return {
    id: 7,
    review_status: "inbox",
    event: {
      id: 1,
      name: "Concert",
      start: "2026-10-24T09:42:00",
      allday: false,
      category_names: [],
      custom_categories: [],
      co_organizers: [],
      report_url: "/event/1/report",
      organization: { id: 2, name: "Other Crew", is_verified: false },
    },
    dates: [],
    auto_verify: false,
    auto_verify_description: "If all upcoming reference requests of Other Crew should be verified automatically.",
    rating_choices: [
      { value: 0, label: "0 (Little relevant)" },
      { value: 50, label: "5 (Default)" },
      { value: 60, label: "6" },
    ],
    default_rating: 50,
    rejection_reasons: [
      { value: 0, label: "No reason" },
      { value: 4, label: "Irrelevant" },
    ],
    list_url: "/manage/admin_unit/3/incoming_event_reference_requests",
    ...overrides,
  };
}

async function mountPage() {
  const wrapper = mount(EventReferenceRequestReviewPage, {
    props: { organizationId: 3, id: 7 },
    attachTo: document.body,
    global: {
      plugins: [
        createBootstrap(),
        createI18n({
          legacy: false,
          locale: "en",
          messages: {
            en: { "Review %(model_display_name)s": "Review {model_display_name}", Cancel: "Cancel" },
          },
        }),
      ],
    },
  });
  await flushPromises();
  return wrapper;
}

const body = (selector: string) => document.body.querySelector<HTMLElement>(selector);

async function open(wrapper: Awaited<ReturnType<typeof mountPage>>, kind: "accept" | "reject") {
  await wrapper.get(`[data-test=${kind}]`).trigger("click");
  await flushPromises();
}

describe("EventReferenceRequestReviewPage", () => {
  enableAutoUnmount(afterEach);

  beforeEach(() => {
    document.body.innerHTML = "";
    [GET, POST, assign].forEach((f) => f.mockReset());
    vi.stubGlobal("location", { assign });
  });

  it("loads the request and shows the cards, decisions and breadcrumb", async () => {
    GET.mockResolvedValue({ data: review() });
    const wrapper = await mountPage();

    expect(GET).toHaveBeenCalledWith(`${BASE}/review`, PARAMS);
    expect(wrapper.text()).toContain("Concert");
    expect(wrapper.find("[data-test=decision]").exists()).toBe(true);
    const crumb = wrapper.get(".breadcrumb a");
    expect(crumb.attributes("href")).toBe("/manage/admin_unit/3/incoming_event_reference_requests");
    expect(wrapper.get(".breadcrumb-item.active").text()).toContain("Review");
  });

  it("shows the load error", async () => {
    GET.mockResolvedValue({ error: { message: "Forbidden" } });
    const wrapper = await mountPage();

    expect(wrapper.get(".alert-danger").text()).toBe("Forbidden");
    expect(wrapper.find("[data-test=decision]").exists()).toBe(false);
  });

  it("accepts with the default rating", async () => {
    GET.mockResolvedValue({ data: review() });
    POST.mockResolvedValue({ data: { redirect_url: "/list" } });
    const wrapper = await mountPage();

    await open(wrapper, "accept");
    expect((body("#rating") as HTMLSelectElement).value).toBe("50");
    body("[data-test=accept-confirm]")!.click();
    await flushPromises();

    expect(POST).toHaveBeenCalledWith(`${BASE}/verify`, {
      ...PARAMS,
      body: { rating: 50, auto_verify: false },
    });
    expect(assign).toHaveBeenCalledWith("/list");
  });

  it("accepts with the chosen rating and the auto-verify switch", async () => {
    GET.mockResolvedValue({ data: review() });
    POST.mockResolvedValue({ data: { redirect_url: "/list" } });
    const wrapper = await mountPage();

    await open(wrapper, "accept");
    const rating = body("#rating") as HTMLSelectElement;
    rating.value = "60";
    rating.dispatchEvent(new Event("change"));
    (body("#auto_verify") as HTMLInputElement).click();
    await flushPromises();
    expect(document.body.textContent).toContain(
      "If all upcoming reference requests of Other Crew should be verified automatically.",
    );
    body("[data-test=accept-confirm]")!.click();
    await flushPromises();

    expect(POST.mock.calls[0][1].body).toEqual({ rating: 60, auto_verify: true });
  });

  it("hides the auto-verify switch when the requester is already verified automatically", async () => {
    GET.mockResolvedValue({ data: review({ auto_verify: true, auto_verify_description: null }) });
    const wrapper = await mountPage();

    await open(wrapper, "accept");

    expect(body("#rating")).not.toBeNull();
    expect(body("#auto_verify")).toBeNull();
  });

  it("rejects without a reason", async () => {
    GET.mockResolvedValue({ data: review() });
    POST.mockResolvedValue({ data: { redirect_url: "/list" } });
    const wrapper = await mountPage();

    await open(wrapper, "reject");
    body("[data-test=reject-confirm]")!.click();
    await flushPromises();

    expect(POST).toHaveBeenCalledWith(`${BASE}/reject`, {
      ...PARAMS,
      body: { rejection_reason: null },
    });
    expect(assign).toHaveBeenCalledWith("/list");
  });

  it("rejects with the chosen reason", async () => {
    GET.mockResolvedValue({ data: review() });
    POST.mockResolvedValue({ data: { redirect_url: "/list" } });
    const wrapper = await mountPage();

    await open(wrapper, "reject");
    const select = body("#rejection_reason") as HTMLSelectElement;
    select.value = "4";
    select.dispatchEvent(new Event("change"));
    await flushPromises();
    body("[data-test=reject-confirm]")!.click();
    await flushPromises();

    expect(POST.mock.calls[0][1].body).toEqual({ rejection_reason: 4 });
  });

  it("shows a server error inline and keeps the page", async () => {
    GET.mockResolvedValue({ data: review() });
    POST.mockResolvedValue({ error: { message: "Request already verified" } });
    const wrapper = await mountPage();

    await open(wrapper, "accept");
    body("[data-test=accept-confirm]")!.click();
    await flushPromises();

    expect(body("[data-test=accept-error]")!.textContent).toContain("Request already verified");
    expect(assign).not.toHaveBeenCalled();
    expect(body("[data-test=accept-confirm]")!.hasAttribute("disabled")).toBe(false);
  });

  it("falls back to a generic error", async () => {
    GET.mockResolvedValue({ data: review() });
    POST.mockResolvedValue({ error: {} });
    const wrapper = await mountPage();

    await open(wrapper, "reject");
    body("[data-test=reject-confirm]")!.click();
    await flushPromises();

    expect(body("[data-test=reject-error]")!.textContent).toContain("Error");
  });
});
