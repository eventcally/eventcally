import { flushPromises } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/shared/boot", () => ({ boot: { base: "/", locale: "en", csrfToken: "x" } }));

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
vi.mock("@/shared/notify", () => ({ useNotify: () => ({ success, error: vi.fn() }) }));

import { mountPage } from "../testing";
import OrganizationApiKeyPage from "./OrganizationApiKeyPage.vue";

const URL = "/manage/admin_unit/3/api_key/5";
const READ = "/bff/manage/organizations/{id}/api-keys/{api_key_id}";
const apiKey = (over = {}) => ({
  id: 5,
  name: "Mein API Key",
  created_at: "2026-11-04T10:00:00Z",
  rate_limits: ["500 per 1 hour: 500 remaining"],
  audit: { created_at: "2026-11-04T10:00:00Z", created_by_label: "me@test.de" },
  can_write: true,
  ...over,
});
const mountIt = () => mountPage(OrganizationApiKeyPage, { organizationId: 3, id: 5 }, URL, { Cancel: "Cancel" });
const items = () => [...document.querySelectorAll<HTMLAnchorElement>(".dropdown-item")];
const openActions = async (wrapper: { find: (s: string) => { trigger: (e: string) => Promise<void> } }) => {
  await wrapper.find("button.dropdown-toggle").trigger("click");
  await flushPromises();
};

describe("OrganizationApiKeyPage", () => {
  const assign = vi.fn();

  beforeEach(() => {
    [GET, POST, PUT, success, assign].forEach((f) => f.mockReset());
    vi.stubGlobal("location", { assign });
    history.replaceState(null, "");
    document.body.innerHTML = "";
  });

  it("shows the key, the rate limit and the audit line, but no key alert", async () => {
    GET.mockResolvedValue({ data: apiKey() });
    const { wrapper } = await mountIt();

    expect(GET).toHaveBeenCalledWith(READ, { params: { path: { id: 3, api_key_id: 5 } } });
    expect(wrapper.find(".breadcrumb").text()).toContain("API key 5");
    expect(wrapper.text()).toContain("Mein API Key");
    expect(wrapper.text()).toContain("500 per 1 hour: 500 remaining");
    expect(wrapper.find("[data-test=created-key]").exists()).toBe(false);
  });

  it("shows the key once after the creation", async () => {
    history.replaceState({ key: "secret-key" }, "");
    GET.mockResolvedValue({ data: apiKey() });
    const { wrapper } = await mountIt();

    expect(wrapper.find("[data-test=created-key]").text()).toContain("secret-key");
    expect(wrapper.find(".alert-success").exists()).toBe(true);
    // Taken out of the history state: a reload does not show it again.
    expect(history.state?.key).toBeUndefined();
  });

  it("offers no actions without permission", async () => {
    GET.mockResolvedValue({ data: apiKey({ can_write: false }) });
    const { wrapper } = await mountIt();

    expect(wrapper.find("button.dropdown-toggle").exists()).toBe(false);
  });

  it("shows the error of a failed load", async () => {
    GET.mockResolvedValue({ error: { message: "Not found" } });
    const { wrapper } = await mountIt();

    expect(wrapper.find(".alert-danger").text()).toBe("Not found");
  });

  it("renames in a modal, toasts and reloads", async () => {
    GET.mockResolvedValue({ data: apiKey() });
    PUT.mockResolvedValue({ data: { message: "API key successfully updated" } });
    const { wrapper } = await mountIt();
    await openActions(wrapper);
    expect(items().map((i) => i.textContent?.trim())).toEqual(["Edit", "Delete"]);
    items()[0].click();
    await flushPromises();

    const input = document.querySelector<HTMLInputElement>(".modal #name")!;
    expect(input.value).toBe("Mein API Key");
    input.value = "Neuer Name";
    input.dispatchEvent(new Event("input"));
    await flushPromises();
    document.querySelector<HTMLButtonElement>(".modal-footer .btn-primary")!.click();
    await flushPromises();

    expect(PUT).toHaveBeenCalledWith(READ, {
      params: { path: { id: 3, api_key_id: 5 } },
      body: { name: "Neuer Name" },
    });
    expect(success).toHaveBeenCalledWith("API key successfully updated");
    expect(GET).toHaveBeenCalledTimes(2);
  });

  it("shows the errors of a failed rename inside the modal", async () => {
    GET.mockResolvedValue({ data: apiKey() });
    const { wrapper } = await mountIt();

    PUT.mockResolvedValueOnce({ error: { errors: [{ loc: ["name"], msg: "Required" }] } });
    await openActions(wrapper);
    items()[0].click();
    await flushPromises();
    document.querySelector<HTMLButtonElement>(".modal-footer .btn-primary")!.click();
    await flushPromises();
    expect(document.querySelector(".modal .invalid-feedback")?.textContent).toContain("Required");

    PUT.mockResolvedValueOnce({ error: { errors: [{ loc: ["other"], msg: "Odd" }] } });
    document.querySelector<HTMLButtonElement>(".modal-footer .btn-primary")!.click();
    await flushPromises();
    expect(document.querySelector("[data-test=api-key-name-error]")?.textContent?.trim()).toBe("Odd");

    PUT.mockResolvedValueOnce({ error: { message: "Forbidden" } });
    document.querySelector<HTMLButtonElement>(".modal-footer .btn-primary")!.click();
    await flushPromises();
    expect(document.querySelector("[data-test=api-key-name-error]")?.textContent?.trim()).toBe("Forbidden");
    expect(success).not.toHaveBeenCalled();
  });

  it("deletes after the typed name and leaves for the list", async () => {
    GET.mockResolvedValue({ data: apiKey() });
    POST.mockResolvedValue({ data: { message: "Gone", redirect_url: "/x" }, response: { ok: true } });
    const { wrapper } = await mountIt();
    await openActions(wrapper);
    items()[1].click();
    await flushPromises();

    expect(document.body.textContent).toContain("Do you want to delete 'API key 5'?");
    const modal = [...document.querySelectorAll(".modal")].find((m) =>
      m.textContent?.includes("Do you want to delete"),
    )!;
    const input = modal.querySelector<HTMLInputElement>("input")!;
    input.value = "Mein API Key";
    input.dispatchEvent(new Event("input"));
    await flushPromises();
    modal.querySelector<HTMLButtonElement>("button[type=submit]")!.click();
    await flushPromises();

    expect(POST).toHaveBeenCalledWith(`${READ}/delete`, {
      params: { path: { id: 3, api_key_id: 5 } },
      body: { name: "Mein API Key", inline: false },
    });
    expect(assign).toHaveBeenCalledWith("/manage/admin_unit/3/api_keys");
  });
});
