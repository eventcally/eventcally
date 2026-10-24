import { flushPromises, mount } from "@vue/test-utils";
import { createBootstrap } from "bootstrap-vue-next";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { defineComponent } from "vue";
import { createI18n } from "vue-i18n";

vi.mock("@/shared/boot", () => ({
  boot: { locale: "en", csrfToken: "x", loginUrl: "/login" },
}));

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

vi.mock("vue-router", () => ({
  RouterLink: defineComponent({ name: "RouterLink", render: () => null }),
}));

import EventReferenceRequestCreatePage from "./EventReferenceRequestCreatePage.vue";

const assign = vi.fn();
const MESSAGES = {
  en: { "Create %(model_display_name)s": "Create {model_display_name}" },
};
const BASE = "/bff/manage/organizations/{id}/events/{event_id}";

async function mountPage() {
  GET.mockImplementation(async (path: string) =>
    path.endsWith("/reference-request-organizations")
      ? { data: { items: [{ id: 9, name: "Other Crew" }] } }
      : {
          data: {
            event: { id: 3, name: "Konzert" },
            list_url: "/manage/admin_unit/5/outgoing_event_reference_requests",
          },
        },
  );
  const wrapper = mount(EventReferenceRequestCreatePage, {
    props: { organizationId: 5, eventId: 3 },
    attachTo: document.body,
    global: {
      plugins: [createBootstrap(), createI18n({ legacy: false, locale: "en", messages: MESSAGES })],
    },
  });
  await flushPromises();
  return wrapper;
}

async function pickOrganization(wrapper: Awaited<ReturnType<typeof mountPage>>) {
  await wrapper.find("#admin_unit").setValue("Oth");
  await vi.advanceTimersByTimeAsync(300);
  await flushPromises();
  await wrapper.find("[data-test=option]").trigger("click");
}

describe("EventReferenceRequestCreatePage", () => {
  beforeEach(() => {
    [GET, POST, PUT, assign].forEach((f) => f.mockReset());
    vi.stubGlobal("location", { assign });
    vi.useRealTimers();
    Element.prototype.scrollIntoView = vi.fn();
  });

  it("loads the form with the instruction and breadcrumb", async () => {
    const wrapper = await mountPage();

    expect(GET.mock.calls[0]).toEqual([
      `${BASE}/reference-request-form`,
      { params: { path: { id: 5, event_id: 3 } } },
    ]);
    expect(wrapper.text()).toContain(
      "Ask another organization to reference your event on their calendar.",
    );
    expect(wrapper.find(".breadcrumb").text()).toContain("Create Event reference request");
    expect(wrapper.find(".breadcrumb a").attributes("href")).toBe(
      "/manage/admin_unit/5/outgoing_event_reference_requests",
    );
  });

  it("requests the reference from the picked organization", async () => {
    vi.useFakeTimers();
    POST.mockResolvedValue({
      data: { id: 1, verified: false, redirect_url: "/list" },
    });
    const wrapper = await mountPage();

    await pickOrganization(wrapper);
    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(GET).toHaveBeenCalledWith(`${BASE}/reference-request-organizations`, {
      params: { path: { id: 5, event_id: 3 }, query: { keyword: "Oth" } },
    });
    expect(POST).toHaveBeenCalledWith(`${BASE}/reference-requests`, {
      params: { path: { id: 5, event_id: 3 } },
      body: { admin_unit_id: 9 },
    });
    expect(assign).toHaveBeenCalledWith("/list");
  });

  it("shows the field error of a missing organization", async () => {
    POST.mockResolvedValue({
      error: {
        errors: [{ loc: ["admin_unit_id"], msg: "This field is required." }],
      },
    });
    const wrapper = await mountPage();

    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(POST.mock.calls[0][1].body).toEqual({ admin_unit_id: null });
    expect(wrapper.find("[data-test=target-error]").text()).toBe("This field is required.");
  });

  it("shows unmatched, integrity and generic errors as an alert", async () => {
    POST.mockResolvedValueOnce({
      error: { errors: [{ loc: ["body"], msg: "Broken" }] },
    });
    POST.mockResolvedValueOnce({
      error: { message: "Action violates database integrity." },
    });
    POST.mockResolvedValueOnce({ error: {} });
    const wrapper = await mountPage();

    await wrapper.find("form").trigger("submit");
    await flushPromises();
    expect(wrapper.find("[data-test=save-error]").text()).toBe("Broken");

    await wrapper.find("form").trigger("submit");
    await flushPromises();
    expect(wrapper.find("[data-test=save-error]").text()).toBe(
      "Action violates database integrity.",
    );

    await wrapper.find("form").trigger("submit");
    await flushPromises();
    expect(wrapper.find("[data-test=save-error]").text()).toBe("Error");
    expect(assign).not.toHaveBeenCalled();
  });

  it("reports a load error", async () => {
    GET.mockResolvedValue({ error: { message: "Forbidden" } });
    const wrapper = mount(EventReferenceRequestCreatePage, {
      props: { organizationId: 5, eventId: 3 },
      global: {
        plugins: [
          createBootstrap(),
          createI18n({ legacy: false, locale: "en", messages: MESSAGES }),
        ],
      },
    });
    await flushPromises();
    expect(wrapper.text()).toContain("Forbidden");
    expect(wrapper.find("form").exists()).toBe(false);

    GET.mockResolvedValue({});
    const fallback = mount(EventReferenceRequestCreatePage, {
      props: { organizationId: 5, eventId: 3 },
      global: {
        plugins: [
          createBootstrap(),
          createI18n({ legacy: false, locale: "en", messages: MESSAGES }),
        ],
      },
    });
    await flushPromises();
    expect(fallback.text()).toContain("Error");
  });
});
