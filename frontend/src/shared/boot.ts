import { createBootstrap } from "bootstrap-vue-next";
// Component styles of bootstrap-vue-next only (toast, modal, ...); Bootstrap itself comes from the Jinja frame.
import "bootstrap-vue-next/dist/bootstrap-vue-next.css";
import { createApp, type Component } from "vue";
import type { Router } from "vue-router";
import { i18n } from "./i18n";

export interface Boot {
  base: string;
  bffBase: string;
  locale: string;
  csrfToken: string;
  user: { email: string; roles: string[] } | null;
  loginUrl: string;
  docsUrl: string | null;
}

export function readBoot(): Boot {
  const el = document.getElementById("boot");
  if (!el?.textContent) throw new Error("Missing #boot data");
  return JSON.parse(el.textContent) as Boot;
}

export const boot: Boot = readBoot();

/** Create and mount an app on `#app`. Bootstrap CSS comes from the Jinja frame. */
export function mountApp(App: Component, { router }: { router: Router }) {
  const app = createApp(App);
  app.use(i18n);
  app.use(router);
  app.use(createBootstrap());
  app.mount("#app");
  return app;
}
