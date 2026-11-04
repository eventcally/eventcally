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
import ProfilePage from "./ProfilePage.vue";

const assign = vi.fn();

beforeEach(() => {
  [GET, POST, PUT, assign].forEach((f) => f.mockReset());
  vi.stubGlobal("location", { assign });
  document.body.innerHTML = "";
  sessionStorage.clear();
});

const profile = (over = {}) => ({
  data: {
    email: "test@test.de",
    locale: null,
    newsletter_enabled: true,
    deletion_requested_at: null,
    ...over,
  },
});

describe("ProfilePage", () => {
  it("shows the email and the four groups of links", async () => {
    GET.mockResolvedValue(profile());
    const { wrapper } = await mountPage(ProfilePage);

    expect(GET).toHaveBeenCalledWith("/bff/user/profile");
    expect(wrapper.find("h1").text()).toBe("test@test.de");
    expect(wrapper.findAll("h2").map((h) => h.text())).toEqual([
      "Profile",
      "Settings",
      "Organizations",
      "Developer",
    ]);
    const links = wrapper.findAll("a.list-group-item").map((a) => a.attributes("href"));
    expect(links).toEqual([
      "/change",
      "/user/request-deletion",
      "/user/general",
      "/user/notifications",
      "/user/oauth2_tokens",
      "/user/organization_members",
      "/user/organization_member_invitations",
      "/user/organization_invitations",
      "/user/oauth2_clients",
      "/user/api_keys",
    ]);
    expect(wrapper.find(".alert").exists()).toBe(false);
  });

  it("shows the requested deletion with the way to cancel it", async () => {
    GET.mockResolvedValue(profile({ deletion_requested_at: "2026-11-03T10:00:00Z" }));
    const { wrapper } = await mountPage(ProfilePage);

    expect(wrapper.find(".alert-danger").text()).toContain(
      "Your account is scheduled for deletion.",
    );
    expect(wrapper.find(".alert-danger a").attributes("href")).toBe("/user/cancel-deletion");
    expect(wrapper.find('a[href="/user/request-deletion"]').exists()).toBe(false);
  });

  it("shows the error", async () => {
    GET.mockResolvedValue({ error: { message: "Forbidden" } });
    const { wrapper } = await mountPage(ProfilePage);

    expect(wrapper.find(".alert-danger").text()).toBe("Forbidden");
  });
});
