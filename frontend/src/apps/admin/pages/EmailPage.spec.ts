import { flushPromises, mount } from "@vue/test-utils";
import { createBootstrap } from "bootstrap-vue-next";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createI18n } from "vue-i18n";
import { createMemoryHistory, createRouter } from "vue-router";

vi.mock("@/shared/boot", () => ({ boot: { locale: "en", csrfToken: "x", loginUrl: "/login" } }));

const GET = vi.fn();
const POST = vi.fn();
vi.mock("@/shared/api", () => ({
  api: { GET: (...a: unknown[]) => GET(...a), POST: (...a: unknown[]) => POST(...a) },
}));

const success = vi.fn();
vi.mock("@/shared/notify", () => ({ useNotify: () => ({ success, error: vi.fn() }) }));

import EmailPage from "./EmailPage.vue";

const config = {
  suppress_send: false,
  server: "smtp.test",
  port: 587,
  use_tls: true,
  use_ssl: false,
  username: null,
  password_set: true,
  default_sender: "EventCally <info@test.de>",
};

async function mountPage() {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/", name: "home", component: { template: "<div/>" } },
      { path: "/email", name: "email", component: EmailPage },
    ],
  });
  router.push("/email");
  await router.isReady();
  const wrapper = mount(EmailPage, {
    global: {
      plugins: [router, createBootstrap(), createI18n({ legacy: false, locale: "en", messages: { en: {} } })],
    },
  });
  await flushPromises();
  return wrapper;
}

const buttons = (wrapper: Awaited<ReturnType<typeof mountPage>>) => wrapper.findAll("button");

describe("EmailPage", () => {
  beforeEach(() => {
    GET.mockReset().mockResolvedValue({ data: config });
    POST.mockReset();
    success.mockReset();
  });

  it("shows the config and masks the password", async () => {
    const wrapper = await mountPage();
    const text = wrapper.find("table").text();

    expect(text).toContain("MAIL_SERVER");
    expect(text).toContain("smtp.test");
    expect(text).toContain("587");
    expect(text).toContain("••••••");
    expect(wrapper.find("table").text()).toContain("MAIL_USERNAME");
    expect(text).toMatch(/MAIL_USERNAME\s*Not specified/);
  });

  it("shows Not specified when no password is set", async () => {
    GET.mockResolvedValue({ data: { ...config, password_set: false } });
    const wrapper = await mountPage();

    expect(wrapper.find("table").text()).not.toContain("••••••");
    expect(wrapper.find("table").text()).toMatch(/MAIL_PASSWORD\s*Not specified/);
  });

  it("sends a test mail synchronously and toasts", async () => {
    POST.mockResolvedValue({ data: { job_id: null, count: 1 } });
    const wrapper = await mountPage();

    await wrapper.find("input[type=email]").setValue("to@test.de");
    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(POST).toHaveBeenCalledWith("/bff/admin/email/test", {
      body: { recipient: "to@test.de", asynchronous: false },
    });
    expect(success).toHaveBeenCalledWith("Mail sent successfully");
  });

  it("shows the delivery error inline", async () => {
    POST.mockResolvedValue({ error: { name: "MailDeliveryError", message: "SMTP down" } });
    const wrapper = await mountPage();

    await wrapper.find("input[type=email]").setValue("to@test.de");
    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(wrapper.find(".alert-danger").text()).toBe("SMTP down");
    expect(success).not.toHaveBeenCalled();
  });

  it("maps a recipient validation error to the input", async () => {
    POST.mockResolvedValue({
      error: { name: "Unprocessable Entity", message: "x", errors: [{ loc: ["recipient"], msg: "Bad address" }] },
    });
    const wrapper = await mountPage();

    await wrapper.find("input[type=email]").setValue("to@test.de");
    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(wrapper.find(".invalid-feedback").text()).toBe("Bad address");
  });

  it("sends asynchronously and shows the result", async () => {
    POST.mockResolvedValue({ data: { job_id: null, count: 1 } });
    const wrapper = await mountPage();

    await wrapper.find("input[type=email]").setValue("to@test.de");
    await buttons(wrapper)[1].trigger("click");
    await flushPromises();

    expect(POST).toHaveBeenCalledWith("/bff/admin/email/test", {
      body: { recipient: "to@test.de", asynchronous: true },
    });
    expect(wrapper.find(".alert-success").text()).toContain("Mails sent successfully");
  });
});
