import { flushPromises, mount } from "@vue/test-utils";
import { createBootstrap } from "bootstrap-vue-next";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createI18n } from "vue-i18n";

vi.mock("@/shared/boot", () => ({ boot: { locale: "en", csrfToken: "x", loginUrl: "/login" } }));

const GET = vi.fn();
const POST = vi.fn();
vi.mock("@/shared/api", () => ({
  api: { GET: (...a: unknown[]) => GET(...a), POST: (...a: unknown[]) => POST(...a) },
}));

const success = vi.fn();
vi.mock("@/shared/notify", () => ({ useNotify: () => ({ success, error: vi.fn() }) }));

import EventReportPage from "./EventReportPage.vue";

async function mountPage() {
  const wrapper = mount(EventReportPage, {
    props: { id: 7 },
    global: {
      plugins: [createBootstrap(), createI18n({ legacy: false, locale: "en", messages: { en: {} } })],
    },
  });
  await flushPromises();
  return wrapper;
}

async function fill(wrapper: Awaited<ReturnType<typeof mountPage>>) {
  await wrapper.find('input[name="contactName"]').setValue("Firstname Lastname");
  await wrapper.find('input[name="contactEmail"]').setValue("a@test.de");
  await wrapper.find('textarea[name="message"]').setValue("This event will not take place.");
}

describe("EventReportPage", () => {
  beforeEach(() => {
    GET.mockReset().mockResolvedValue({ data: { event_id: 7, event_name: "Jam Session" } });
    POST.mockReset();
    success.mockReset();
  });

  it("loads the event and links to it", async () => {
    const wrapper = await mountPage();

    expect(GET).toHaveBeenCalledWith("/bff/public/events/{id}/report-form", {
      params: { path: { id: 7 } },
    });
    expect(wrapper.find('a[href="/event/7"]').text()).toBe("Jam Session");
  });

  it("posts the report and replaces the form with a success message", async () => {
    POST.mockResolvedValue({ response: { ok: true } });
    const wrapper = await mountPage();
    await fill(wrapper);

    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(POST).toHaveBeenCalledWith("/bff/public/events/{id}/reports", {
      params: { path: { id: 7 } },
      body: {
        contact_name: "Firstname Lastname",
        contact_email: "a@test.de",
        message: "This event will not take place.",
      },
    });
    expect(success).toHaveBeenCalledWith("Event successfully reported");
    expect(wrapper.find("button[type=submit]").exists()).toBe(false);
    expect(wrapper.find(".alert-success").text()).toContain("Event successfully reported");
  });

  it("shows field errors from a 422", async () => {
    POST.mockResolvedValue({
      error: { errors: [{ loc: ["message"], msg: "Too short" }] },
      response: { ok: false },
    });
    const wrapper = await mountPage();
    await fill(wrapper);

    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(wrapper.text()).toContain("Too short");
    expect(success).not.toHaveBeenCalled();
    expect(wrapper.find("button[type=submit]").exists()).toBe(true);
  });

  it("shows the message of other errors such as the rate limit", async () => {
    POST.mockResolvedValue({
      error: { name: "Too Many Requests", message: "5 per 1 minute" },
      response: { ok: false },
    });
    const wrapper = await mountPage();
    await fill(wrapper);

    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(wrapper.find(".alert-danger").text()).toBe("5 per 1 minute");
  });
});
