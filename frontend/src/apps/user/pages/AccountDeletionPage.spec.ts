import { flushPromises } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/shared/boot", () => ({
  boot: { base: "/", locale: "en", csrfToken: "x", loginUrl: "/login" },
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

import { mountPage } from "../testing";
import AccountDeletionPage from "./AccountDeletionPage.vue";

const assign = vi.fn();

beforeEach(() => {
  [GET, POST, PUT, assign].forEach((f) => f.mockReset());
  vi.stubGlobal("location", { assign });
  document.body.innerHTML = "";
  sessionStorage.clear();
});

describe("AccountDeletionPage", () => {
  it("requests the deletion with the typed email", async () => {
    POST.mockResolvedValue({ data: { redirect_url: "/profile" } });
    const { wrapper } = await mountPage(AccountDeletionPage, {
      mode: "request",
    });

    expect(wrapper.text()).toContain("The account is not deleted immediately.");
    expect(wrapper.find("#submit").text()).toBe("Request deletion");
    await wrapper.find("#email").setValue("test@test.de");
    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(POST).toHaveBeenCalledWith("/bff/user/deletion", {
      body: { email: "test@test.de" },
    });
    expect(assign).toHaveBeenCalledWith("/profile");
  });

  it("cancels the deletion", async () => {
    POST.mockResolvedValue({ data: { redirect_url: "/profile" } });
    const { wrapper } = await mountPage(AccountDeletionPage, {
      mode: "cancel",
    });

    expect(wrapper.find("p").exists()).toBe(false);
    expect(wrapper.find("#submit").text()).toBe("Cancel deletion");
    await wrapper.find("#email").setValue("test@test.de");
    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(POST).toHaveBeenCalledWith("/bff/user/deletion/cancel", {
      body: { email: "test@test.de" },
    });
  });

  it("shows the mismatch at the field", async () => {
    POST.mockResolvedValue({
      error: {
        errors: [{ loc: ["email"], msg: "Entered email does not match your email" }],
      },
    });
    const { wrapper } = await mountPage(AccountDeletionPage, {
      mode: "request",
    });

    await wrapper.find("#email").setValue("wrong");
    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(wrapper.find("[data-test=field-error]").text()).toBe(
      "Entered email does not match your email",
    );
    expect(assign).not.toHaveBeenCalled();
  });

  it("shows other refusals as an alert", async () => {
    POST.mockResolvedValue({
      error: { message: "You are administrator of at least one organization." },
    });
    const { wrapper } = await mountPage(AccountDeletionPage, {
      mode: "request",
    });

    await wrapper.find("#email").setValue("test@test.de");
    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(wrapper.find(".alert-danger").text()).toContain("administrator");
  });

  it("shows unmapped field errors as an alert", async () => {
    POST.mockResolvedValue({
      error: { errors: [{ loc: ["other"], msg: "Odd" }] },
    });
    const { wrapper } = await mountPage(AccountDeletionPage, {
      mode: "cancel",
    });

    await wrapper.find("#email").setValue("test@test.de");
    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(wrapper.find(".alert-danger").text()).toBe("Odd");
  });
});
