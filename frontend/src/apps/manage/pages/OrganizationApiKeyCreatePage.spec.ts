import { flushPromises } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/shared/boot", () => ({ boot: { base: "/", locale: "en", csrfToken: "x" } }));

const POST = vi.fn();
vi.mock("@/shared/api", () => ({ api: { POST: (...a: unknown[]) => POST(...a) } }));

import { mountPage } from "../testing";
import OrganizationApiKeyCreatePage from "./OrganizationApiKeyCreatePage.vue";

const URL = "/manage/admin_unit/3/api_key/create";
const CREATE = "/bff/manage/organizations/{id}/api-keys";

describe("OrganizationApiKeyCreatePage", () => {
  beforeEach(() => POST.mockReset());

  it("creates the key and hands it to the read page through the history state", async () => {
    POST.mockResolvedValue({ data: { id: 9, key: "secret-key" } });
    const { wrapper, router } = await mountPage(OrganizationApiKeyCreatePage, { organizationId: 3 }, URL);
    const push = vi.spyOn(router, "push");

    expect(wrapper.find(".breadcrumb").text()).toContain("Create API key");
    await wrapper.find("#name").setValue("Neuer Key");
    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(POST).toHaveBeenCalledWith(CREATE, {
      params: { path: { id: 3 } },
      body: { name: "Neuer Key" },
    });
    expect(push).toHaveBeenCalledWith({
      name: "organization-api-key",
      params: { organizationId: 3, id: 9 },
      state: { key: "secret-key" },
    });
  });

  it("shows a field error at the name", async () => {
    POST.mockResolvedValue({ error: { errors: [{ loc: ["name"], msg: "Required" }] } });
    const { wrapper } = await mountPage(OrganizationApiKeyCreatePage, { organizationId: 3 }, URL);
    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(wrapper.find(".invalid-feedback").text()).toContain("Required");
    expect(wrapper.find("#submit").attributes("disabled")).toBeUndefined();
  });

  it("shows the message of another error such as the key limit", async () => {
    POST.mockResolvedValue({ error: { message: "The maximum number of API keys was reached." } });
    const { wrapper } = await mountPage(OrganizationApiKeyCreatePage, { organizationId: 3 }, URL);
    await wrapper.find("#name").setValue("Noch ein Key");
    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(wrapper.find(".alert-danger").text()).toBe("The maximum number of API keys was reached.");
  });

  it("shows unmatched field errors as the page error", async () => {
    POST.mockResolvedValue({ error: { errors: [{ loc: ["other"], msg: "Odd" }] } });
    const { wrapper } = await mountPage(OrganizationApiKeyCreatePage, { organizationId: 3 }, URL);
    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(wrapper.find(".alert-danger").text()).toBe("Odd");
  });

  it("ignores a second submit while saving", async () => {
    let resolve: (v: unknown) => void = () => {};
    POST.mockReturnValue(new Promise((r) => (resolve = r)));
    const { wrapper } = await mountPage(OrganizationApiKeyCreatePage, { organizationId: 3 }, URL);
    await wrapper.find("form").trigger("submit");
    await wrapper.find("form").trigger("submit");
    resolve({ error: { message: "x" } });
    await flushPromises();

    expect(POST).toHaveBeenCalledTimes(1);
  });
});
