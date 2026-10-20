import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const boot = vi.hoisted(() => ({ locale: "en", csrfToken: "tok", loginUrl: "/login" }));
vi.mock("./boot", () => ({ boot }));

import { authMiddleware } from "./api";

const assign = vi.fn();

function run(method: string) {
  const request = new Request("http://localhost/bff/x", { method });
  return authMiddleware.onRequest!({ request } as never) as Promise<Request> | Request;
}

function respond(status: number) {
  return authMiddleware.onResponse!({ response: new Response(null, { status }) } as never);
}

describe("authMiddleware", () => {
  beforeEach(() => {
    assign.mockReset();
    boot.loginUrl = "/login";
    vi.stubGlobal("location", { assign, pathname: "/admin-next/users" });
  });
  afterEach(() => vi.unstubAllGlobals());

  it("sends the CSRF token on unsafe methods only", async () => {
    expect(((await run("DELETE")) as Request).headers.get("X-CSRFToken")).toBe("tok");
    expect(((await run("GET")) as Request).headers.get("X-CSRFToken")).toBeNull();
  });

  it("redirects a 401 to the login page", async () => {
    await respond(401);

    expect(assign).toHaveBeenCalledWith("/login?next=%2Fadmin-next%2Fusers");
  });

  it("does not follow a login url that leaves the origin", async () => {
    for (const url of ["//evil.example", "https://evil.example", "javascript:alert(1)"]) {
      boot.loginUrl = url;
      await respond(401);
    }

    expect(assign).not.toHaveBeenCalled();
  });

  it("leaves other responses alone", async () => {
    await respond(200);

    expect(assign).not.toHaveBeenCalled();
  });
});
