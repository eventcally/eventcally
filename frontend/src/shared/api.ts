import createClient, { type Middleware } from "openapi-fetch";
import type { paths } from "@/api/schema";
import { legacy } from "./legacy";
import { boot } from "./boot";

const UNSAFE = new Set(["POST", "PUT", "PATCH", "DELETE"]);

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
      location.assign(`${legacy.login}?next=${encodeURIComponent(location.pathname)}`);
    }
    return response;
  },
};

export const api = createClient<paths>({ baseUrl: "" });
api.use(authMiddleware);
