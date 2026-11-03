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
import AcceptTosPage from "./AcceptTosPage.vue";

const assign = vi.fn();

beforeEach(() => {
  [GET, POST, PUT, assign].forEach((f) => f.mockReset());
  vi.stubGlobal("location", { assign });
  document.body.innerHTML = "";
  sessionStorage.clear();
});

const messages = {
  "I read and accept %(tos_open)sTerms of Service%(tos_close)s and %(privacy_open)sPrivacy%(privacy_close)s.":
    "I read and accept {tos_open}Terms of Service{tos_close} and {privacy_open}Privacy{privacy_close}.",
  "I read and accept %(privacy_open)sPrivacy%(privacy_close)s.":
    "I read and accept {privacy_open}Privacy{privacy_close}.",
};

describe("AcceptTosPage", () => {
  it("shows the terms when there are some", async () => {
    GET.mockResolvedValue({ data: { has_tos: true } });
    const { wrapper } = await mountPage(AcceptTosPage, {}, "/user/accept-tos", messages);

    expect(wrapper.find("label").text()).toBe("I read and accept Terms of Service and Privacy.");
    expect(wrapper.find("#accept_tos").attributes("required")).toBeDefined();
  });

  it("confirms with the checkbox and follows `next`", async () => {
    GET.mockResolvedValue({ data: { has_tos: false } });
    POST.mockResolvedValue({ data: { redirect_url: "/manage" } });
    const { wrapper } = await mountPage(
      AcceptTosPage,
      { next: "/manage" },
      "/user/accept-tos?next=/manage",
      messages,
    );

    expect(wrapper.find("label").text()).toBe("I read and accept Privacy.");

    // Without the checkbox nothing is sent.
    await wrapper.find("form").trigger("submit");
    await flushPromises();
    expect(POST).not.toHaveBeenCalled();

    await wrapper.find("#accept_tos").setValue(true);
    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(POST).toHaveBeenCalledWith("/bff/user/accept-tos", {
      params: { query: { next: "/manage" } },
      body: { accept_tos: true },
    });
    expect(assign).toHaveBeenCalledWith("/manage");
  });

  it("shows a failed confirmation", async () => {
    GET.mockResolvedValue({ data: { has_tos: false } });
    POST.mockResolvedValue({ error: { message: "Nope" } });
    const { wrapper } = await mountPage(AcceptTosPage, {}, "/user/accept-tos", messages);

    await wrapper.find("#accept_tos").setValue(true);
    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(wrapper.find(".alert-danger").text()).toBe("Nope");
    expect(assign).not.toHaveBeenCalled();
  });

  it("shows a failed load", async () => {
    GET.mockResolvedValue({ error: {} });
    const { wrapper } = await mountPage(AcceptTosPage, {}, "/user/accept-tos");

    expect(wrapper.find(".alert-danger").text()).toBe("Error");
    expect(wrapper.find("form").exists()).toBe(false);
  });
});
