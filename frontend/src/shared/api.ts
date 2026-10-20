import createClient, { type Middleware } from "openapi-fetch";
import type { paths } from "@/api/schema";
import { boot } from "./boot";

const UNSAFE = new Set(["POST", "PUT", "PATCH", "DELETE"]);

/** The boot data is DOM text: only ever redirect to a path on this origin. */
function loginRedirect(): string | null {
  try {
    const url = new URL(boot.loginUrl, location.origin);
    if (url.origin !== location.origin) return null;
    url.searchParams.set("next", location.pathname);
    return url.pathname + url.search;
  } catch {
    return null;
  }
}

export const authMiddleware: Middleware = {
  onRequest({ request }) {
    request.headers.set("Accept", "application/json");
    if (UNSAFE.has(request.method)) {
      request.headers.set("X-CSRFToken", boot.csrfToken);
    }
    return request;
  },
  onResponse({ response }) {
    if (response.status === 401) {
      const target = loginRedirect();
      if (target) location.assign(target);
    }
    return response;
  },
};

export const api = createClient<paths>({ baseUrl: "" });
api.use(authMiddleware);
