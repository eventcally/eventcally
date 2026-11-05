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

import { setFlash } from "@/shared/flash";
import { mountPage } from "../testing";
import ApiKeyPage from "./ApiKeyPage.vue";

const assign = vi.fn();

beforeEach(() => {
  [GET, POST, PUT, assign, success].forEach((f) => f.mockReset());
  vi.stubGlobal("location", { assign });
  document.body.innerHTML = "";
  sessionStorage.clear();
});

const key = {
  data: {
    id: 5,
    name: "Mein Key",
    created_at: "2026-11-03T14:41:00Z",
    rate_limits: ["500 per 1 hour: 500 remaining"],
    audit: {
      created_at: "2026-11-03T14:41:00Z",
      created_by_label: "test@test.de",
    },
  },
};
const messages = {
  "Please note the key: %(key)s. It will only be displayed once.":
    "Please note the key: {key}. It will only be displayed once.",
  "%(model_display_name)s successfully created": "{model_display_name} successfully created",
  "Created at %(created_at)s by %(created_by)s.": "Created at {created_at} by {created_by}.",
};

describe("ApiKeyPage", () => {
  beforeEach(() => history.replaceState(null, ""));

  it("shows the key, the rate limit and the actions", async () => {
    GET.mockResolvedValue(key);
    const { wrapper } = await mountPage(ApiKeyPage, { id: 5 }, "/user/api_key/5", messages);

    expect(GET).toHaveBeenCalledWith("/bff/user/api-keys/{id}", {
      params: { path: { id: 5 } },
    });
    expect(wrapper.text()).toContain("Mein Key");
    expect(wrapper.text()).toContain("500 per 1 hour: 500 remaining");
    expect(wrapper.find('a[href="/user/api_key/5/update"]').exists()).toBe(true);
    expect(wrapper.find('a[href="/user/api_key/5/delete"]').exists()).toBe(true);
    expect(wrapper.find("[data-test=audit]").text()).toContain("by test@test.de");
    expect(wrapper.find("[data-test=created-key]").exists()).toBe(false);
  });

  it("shows the new key once, right after the creation", async () => {
    GET.mockResolvedValue(key);
    history.replaceState({ key: "SECRET123" }, "");
    const { wrapper } = await mountPage(ApiKeyPage, { id: 5 }, "/user/api_key/5", messages);

    expect(wrapper.find("[data-test=created-key]").text()).toBe(
      "Please note the key: SECRET123. It will only be displayed once.",
    );
    expect(wrapper.find(".alert-success").text()).toBe("API key successfully created");
    // Taken out of the history state: a reload does not show it again.
    expect(history.state?.key).toBeUndefined();
  });

  it("shows the message of an update", async () => {
    GET.mockResolvedValue(key);
    setFlash("API key successfully updated");
    await mountPage(ApiKeyPage, { id: 5 }, "/user/api_key/5", messages);

    expect(success).toHaveBeenCalledWith("API key successfully updated");
  });

  it("shows the error", async () => {
    GET.mockResolvedValue({ error: { message: "Forbidden" } });
    const { wrapper } = await mountPage(ApiKeyPage, { id: 5 }, "/user/api_key/5", messages);

    expect(wrapper.find(".alert-danger").text()).toBe("Forbidden");
  });
});
