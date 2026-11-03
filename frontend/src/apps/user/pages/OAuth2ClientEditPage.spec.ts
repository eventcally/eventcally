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
import OAuth2ClientEditPage from "./OAuth2ClientEditPage.vue";

const assign = vi.fn();

beforeEach(() => {
  [GET, POST, PUT, assign, success].forEach((f) => f.mockReset());
  vi.stubGlobal("location", { assign });
  document.body.innerHTML = "";
  sessionStorage.clear();
});

const client = {
  data: {
    id: 3,
    client_name: "Mein Client",
    redirect_uris: ["/a", "/b"],
    scopes: ["openid"],
    scope: "openid",
    client_id: "x",
    grant_types: [],
    response_types: [],
    token_endpoint_auth_method: [],
  },
};

function route(clientAnswer: unknown = client) {
  GET.mockImplementation((path: string) =>
    Promise.resolve(
      path === "/bff/user/oauth2-clients/form"
        ? { data: { scopes: ["openid", "profile"] } }
        : clientAnswer,
    ),
  );
}

describe("OAuth2ClientEditPage", () => {
  it("creates a client with the lines of the textarea as URIs", async () => {
    route();
    POST.mockResolvedValue({ data: { id: 8 } });
    const { wrapper, router } = await mountPage(
      OAuth2ClientEditPage,
      {},
      "/user/oauth2_client/create",
    );

    await wrapper.find("#client_name").setValue("Neu");
    await wrapper.find("#redirect_uris").setValue("/x\n/y");
    await wrapper.find("#scope-1").setValue(true);
    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(POST).toHaveBeenCalledWith("/bff/user/oauth2-clients", {
      body: {
        client_name: "Neu",
        redirect_uris: ["/x", "/y"],
        scopes: ["profile"],
      },
    });
    expect(router.currentRoute.value.fullPath).toBe("/user/oauth2_client/8");
    expect(takeFlash()).toBe("OAuth2 client successfully created");
  });

  it("prefills and updates a client", async () => {
    route();
    PUT.mockResolvedValue({ response: { ok: true } });
    const { wrapper, router } = await mountPage(
      OAuth2ClientEditPage,
      { id: 3 },
      "/user/oauth2_client/3/update",
    );

    expect(wrapper.find<HTMLInputElement>("#client_name").element.value).toBe("Mein Client");
    expect(wrapper.find<HTMLTextAreaElement>("#redirect_uris").element.value).toBe("/a\n/b");
    expect(wrapper.find<HTMLInputElement>("#scope-0").element.checked).toBe(true);
    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(PUT).toHaveBeenCalledWith("/bff/user/oauth2-clients/{id}", {
      params: { path: { id: 3 } },
      body: {
        client_name: "Mein Client",
        redirect_uris: ["/a", "/b"],
        scopes: ["openid"],
      },
    });
    expect(router.currentRoute.value.fullPath).toBe("/user/oauth2_client/3");
    expect(takeFlash()).toBe("OAuth2 client successfully updated");
  });

  it("shows field errors and other errors of a failed save", async () => {
    route();
    POST.mockResolvedValue({
      error: {
        errors: [
          { loc: ["client_name"], msg: "Required" },
          { loc: ["x"], msg: "Odd" },
        ],
      },
    });
    const { wrapper } = await mountPage(OAuth2ClientEditPage, {}, "/user/oauth2_client/create");

    await wrapper.find("form").trigger("submit");
    await flushPromises();
    expect(wrapper.find("[data-test=field-error]").text()).toBe("Required");
    expect(wrapper.find(".alert-danger").text()).toBe("Odd");

    PUT.mockResolvedValue({
      response: { ok: false },
      error: { message: "Forbidden" },
    });
    const update = await mountPage(OAuth2ClientEditPage, { id: 3 }, "/user/oauth2_client/3/update");
    await update.wrapper.find("form").trigger("submit");
    await flushPromises();
    expect(update.wrapper.find(".alert-danger").text()).toBe("Forbidden");
  });

  it("shows a failed load of the form or of the client", async () => {
    GET.mockResolvedValue({ error: { message: "No form" } });
    const noForm = await mountPage(OAuth2ClientEditPage, {}, "/user/oauth2_client/create");
    expect(noForm.wrapper.find(".alert-danger").text()).toBe("No form");

    route({ error: { message: "No client" } });
    const noClient = await mountPage(
      OAuth2ClientEditPage,
      { id: 3 },
      "/user/oauth2_client/3/update",
    );
    expect(noClient.wrapper.find(".alert-danger").text()).toBe("No client");
    expect(noClient.wrapper.find("form").exists()).toBe(false);
  });
});
