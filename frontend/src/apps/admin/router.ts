import { createRouter, createWebHistory } from "vue-router";
import { boot } from "@/shared/boot";
import { legacy } from "./legacy";
import AdminHome from "./pages/AdminHome.vue";
import UsersPage from "./pages/UsersPage.vue";

export const router = createRouter({
  history: createWebHistory(boot.base),
  routes: [
    { path: "/", name: "home", component: AdminHome },
    { path: "/users", name: "users", component: UsersPage },
    {
      // Strangler fallback: pages that are not migrated yet live under /admin.
      path: "/:rest(.*)*",
      name: "legacy",
      component: AdminHome,
      beforeEnter: (to) => {
        location.assign(legacy.home + to.path);
        return false;
      },
    },
  ],
});
