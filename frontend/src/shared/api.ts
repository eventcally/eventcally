import createClient, { type Middleware } from "openapi-fetch";
import type { paths } from "@/api/schema";
import { boot } from "./boot";

const UNSAFE = new Set(["POST", "PUT", "PATCH", "DELETE"]);

/** The boot data is DOM text: only follow a same-origin path, never `//host` or `javascript:`. */
function isLocalPath(url: string): boolean {
  return url.startsWith("/") && !url.startsWith("//") && !url.startsWith("/\\");
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
    if (response.status === 401 && isLocalPath(boot.loginUrl)) {
      location.assign(`${boot.loginUrl}?next=${encodeURIComponent(location.pathname)}`);
    }
    return response;
  },
};

export const api = createClient<paths>({ baseUrl: "" });
api.use(authMiddleware);
