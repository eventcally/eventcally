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
import NotificationSettingsPage from "./NotificationSettingsPage.vue";

const assign = vi.fn();

beforeEach(() => {
  [GET, POST, PUT, assign].forEach((f) => f.mockReset());
  vi.stubGlobal("location", { assign });
  document.body.innerHTML = "";
  sessionStorage.clear();
});

describe("NotificationSettingsPage", () => {
  it("toggles the newsletter and saves with a full page load", async () => {
    GET.mockResolvedValue({ data: { newsletter_enabled: true } });
    PUT.mockResolvedValue({ data: { redirect_url: "/profile" } });
    const { wrapper } = await mountPage(NotificationSettingsPage);

    expect(wrapper.find<HTMLInputElement>("#newsletter_enabled").element.checked).toBe(true);
    expect(wrapper.text()).toContain("Information about new features and improvements.");
    await wrapper.find("#newsletter_enabled").setValue(false);
    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(PUT).toHaveBeenCalledWith("/bff/user/settings/notifications", {
      body: { newsletter_enabled: false },
    });
    expect(assign).toHaveBeenCalledWith("/profile");
  });

  it("shows a failed save", async () => {
    GET.mockResolvedValue({ data: { newsletter_enabled: false } });
    PUT.mockResolvedValue({ error: { message: "Nope" } });
    const { wrapper } = await mountPage(NotificationSettingsPage);

    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(wrapper.find(".alert-danger").text()).toBe("Nope");
  });

  it("shows a failed load", async () => {
    GET.mockResolvedValue({ error: {} });
    const { wrapper } = await mountPage(NotificationSettingsPage);

    expect(wrapper.find(".alert-danger").text()).toBe("Error");
  });
});
