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
const success = vi.hoisted(() => vi.fn());
vi.mock("@/shared/notify", () => ({
  useNotify: () => ({ success, error: vi.fn() }),
}));

import { takeFlash } from "@/shared/flash";
import { mountPage } from "../testing";
import OAuth2ClientDeletePage from "./OAuth2ClientDeletePage.vue";

const assign = vi.fn();

beforeEach(() => {
  [GET, POST, PUT, assign, success].forEach((f) => f.mockReset());
  vi.stubGlobal("location", { assign });
  document.body.innerHTML = "";
  sessionStorage.clear();
});

const client = { data: { id: 3, client_name: "Mein Client" } };

describe("OAuth2ClientDeletePage", () => {
  it("asks for the name and deletes", async () => {
    GET.mockResolvedValue(client);
    POST.mockResolvedValue({ response: { ok: true } });
    const { wrapper, router } = await mountPage(
      OAuth2ClientDeletePage,
      { id: 3 },
      "/user/oauth2_client/3/delete",
    );

    expect(wrapper.text()).toContain("Do you want to delete 'Mein Client'?");
    await wrapper.find("#name").setValue("Mein Client");
    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(POST).toHaveBeenCalledWith("/bff/user/oauth2-clients/{id}/delete", {
      params: { path: { id: 3 } },
      body: { name: "Mein Client" },
    });
    expect(router.currentRoute.value.fullPath).toBe("/user/oauth2_clients");
    expect(takeFlash()).toBe("OAuth2 client successfully deleted");
  });

  it("shows a mismatch, other errors and a failed load", async () => {
    GET.mockResolvedValueOnce(client);
    POST.mockResolvedValue({
      response: { ok: false },
      error: {
        errors: [
          { loc: ["name"], msg: "Does not match" },
          { loc: ["x"], msg: "Odd" },
        ],
      },
    });
    const { wrapper } = await mountPage(
      OAuth2ClientDeletePage,
      { id: 3 },
      "/user/oauth2_client/3/delete",
    );
    await wrapper.find("#name").setValue("Falsch");
    await wrapper.find("form").trigger("submit");
    await flushPromises();
    expect(wrapper.find("[data-test=field-error]").text()).toBe("Does not match");
    expect(wrapper.find(".alert-danger").text()).toBe("Odd");

    POST.mockResolvedValue({
      response: { ok: false },
      error: { message: "Forbidden" },
    });
    await wrapper.find("form").trigger("submit");
    await flushPromises();
    expect(wrapper.find(".alert-danger").text()).toBe("Forbidden");

    GET.mockResolvedValue({ error: { message: "Gone" } });
    const failed = await mountPage(
      OAuth2ClientDeletePage,
      { id: 3 },
      "/user/oauth2_client/3/delete",
    );
    expect(failed.wrapper.find(".alert-danger").text()).toBe("Gone");
  });
});
