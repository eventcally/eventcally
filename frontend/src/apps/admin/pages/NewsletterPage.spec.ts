import { flushPromises, mount } from "@vue/test-utils";
import { createBootstrap } from "bootstrap-vue-next";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { createI18n } from "vue-i18n";
import { createMemoryHistory, createRouter } from "vue-router";

vi.mock("@/shared/boot", () => ({ boot: { locale: "en", csrfToken: "x", loginUrl: "/login" } }));

const GET = vi.fn();
const POST = vi.fn();
vi.mock("@/shared/api", () => ({
  api: { GET: (...a: unknown[]) => GET(...a), POST: (...a: unknown[]) => POST(...a) },
}));

import NewsletterPage from "./NewsletterPage.vue";

async function mountPage() {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/", name: "home", component: { template: "<div/>" } },
      { path: "/newsletter", name: "newsletter", component: NewsletterPage },
    ],
  });
  router.push("/newsletter");
  await router.isReady();
  const wrapper = mount(NewsletterPage, {
    attachTo: document.body,
    global: {
      plugins: [
        router,
        createBootstrap(),
        createI18n({
          legacy: false,
          locale: "en",
          messages: { en: { "Send to %(count)d recipients?": "Send to {count} recipients?" } },
        }),
      ],
    },
  });
  await flushPromises();
  return wrapper;
}

const modalOk = () => document.body.querySelector<HTMLButtonElement>(".modal-footer .btn-primary");

describe("NewsletterPage", () => {
  beforeEach(() => {
    GET.mockReset();
    POST.mockReset();
  });
  afterEach(() => {
    document.body.innerHTML = "";
  });

  it("sends to the test recipient without a confirmation", async () => {
    POST.mockResolvedValue({ data: { job_id: null, count: 1 } });
    const wrapper = await mountPage();

    await wrapper.find("#newsletter-test-recipient").setValue("t@test.de");
    await wrapper.find("#newsletter-message").setValue("<p>Hi</p>");
    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(POST).toHaveBeenCalledWith("/bff/admin/newsletter", {
      body: { audience: "test", test_recipient: "t@test.de", message: "<p>Hi</p>" },
    });
    expect(wrapper.find(".alert-success").exists()).toBe(true);
  });

  it("hides the recipient input for all users", async () => {
    const wrapper = await mountPage();

    expect(wrapper.find("#newsletter-test-recipient").exists()).toBe(true);
    await wrapper.find("input[type=radio][value=all]").setValue(true);

    expect(wrapper.find("#newsletter-test-recipient").exists()).toBe(false);
  });

  it("sends to all users only after the confirmation", async () => {
    GET.mockResolvedValue({ data: { recipient_count: 3 } });
    POST.mockResolvedValue({ data: { job_id: null, count: 3 } });
    const wrapper = await mountPage();

    await wrapper.find("input[type=radio][value=all]").setValue(true);
    await wrapper.find("#newsletter-message").setValue("Hello");
    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(POST).not.toHaveBeenCalled();
    expect(document.body.querySelector(".modal-body")!.textContent).toContain("Send to 3 recipients?");

    modalOk()!.click();
    await flushPromises();

    expect(POST).toHaveBeenCalledWith("/bff/admin/newsletter", {
      body: { audience: "all", test_recipient: null, message: "Hello" },
    });
    expect(wrapper.find(".alert-success").text()).toContain("(3)");
  });

  it("does not send when the modal says there are no recipients", async () => {
    GET.mockResolvedValue({ data: { recipient_count: 0 } });
    const wrapper = await mountPage();

    await wrapper.find("input[type=radio][value=all]").setValue(true);
    await wrapper.find("#newsletter-message").setValue("Hello");
    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(modalOk()!.disabled).toBe(true);
    expect(POST).not.toHaveBeenCalled();
  });

  it("maps 422 errors to the inputs", async () => {
    POST.mockResolvedValue({
      error: {
        name: "Unprocessable Entity",
        message: "x",
        errors: [
          { loc: ["test_recipient"], msg: "Required" },
          { loc: ["message"], msg: "Too short" },
        ],
      },
    });
    const wrapper = await mountPage();

    await wrapper.find("#newsletter-test-recipient").setValue("t@test.de");
    await wrapper.find("#newsletter-message").setValue("x");
    await wrapper.find("form").trigger("submit");
    await flushPromises();

    const feedback = wrapper.findAll(".invalid-feedback").map((f) => f.text());
    expect(feedback).toEqual(["Required", "Too short"]);
  });

  it("reports an empty result", async () => {
    POST.mockResolvedValue({ data: { job_id: null, count: 0 } });
    const wrapper = await mountPage();

    await wrapper.find("#newsletter-test-recipient").setValue("t@test.de");
    await wrapper.find("#newsletter-message").setValue("x");
    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(wrapper.find(".alert-danger").text()).toBe("There are no recipients.");
  });
});
