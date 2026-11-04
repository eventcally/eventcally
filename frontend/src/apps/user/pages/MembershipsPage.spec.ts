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
import MembershipsPage from "./MembershipsPage.vue";

const assign = vi.fn();

beforeEach(() => {
  [GET, POST, PUT, assign, success].forEach((f) => f.mockReset());
  vi.stubGlobal("location", { assign });
  document.body.innerHTML = "";
  sessionStorage.clear();
});

describe("MembershipsPage", () => {
  it("lists the organizations with a leave link", async () => {
    GET.mockResolvedValue({
      data: {
        items: [
          {
            id: 10,
            organization_id: 7,
            organization_name: "Andere Crew",
            is_admin: false,
          },
        ],
        page: 1,
        per_page: 20,
        total: 1,
        pages: 1,
      },
    });
    const { wrapper } = await mountPage(MembershipsPage, {}, "/user/organization_members");

    expect(wrapper.text()).toContain("Andere Crew");
    expect(wrapper.find('a[href="/user/organization_member/10/delete"]').text()).toBe(
      "Leave organization",
    );
  });

  it("shows the message of a leave and the error", async () => {
    GET.mockResolvedValue({ error: { message: "Forbidden" } });
    setFlash("Organization successfully left");
    const { wrapper } = await mountPage(MembershipsPage, {}, "/user/organization_members");

    expect(success).toHaveBeenCalledWith("Organization successfully left");
    expect(wrapper.find(".alert-danger").text()).toBe("Forbidden");
  });
});
