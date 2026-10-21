import { createRouter, createWebHistory } from "vue-router";
import { boot } from "@/shared/boot";
import { legacy } from "./legacy";
import AdminHome from "./pages/AdminHome.vue";
import EmailPage from "./pages/EmailPage.vue";
import NewsletterPage from "./pages/NewsletterPage.vue";
import OrganizationsPage from "./pages/OrganizationsPage.vue";
import OrganizationUpdatePage from "./pages/OrganizationUpdatePage.vue";
import PlanningPage from "./pages/PlanningPage.vue";
import SettingsPage from "./pages/SettingsPage.vue";
import UsersPage from "./pages/UsersPage.vue";
import UserUpdatePage from "./pages/UserUpdatePage.vue";

export const router = createRouter({
  history: createWebHistory(boot.base),
  routes: [
    { path: "/", name: "home", component: AdminHome },
    { path: "/settings", name: "settings", component: SettingsPage },
    { path: "/email", name: "email", component: EmailPage },
    { path: "/newsletter", name: "newsletter", component: NewsletterPage },
    { path: "/planning", name: "planning", component: PlanningPage },
    { path: "/organizations", name: "organizations", component: OrganizationsPage },
    {
      path: "/organizations/:id(\\d+)/update",
      name: "organization-update",
      component: OrganizationUpdatePage,
      props: (route) => ({ id: Number(route.params.id) }),
    },
    { path: "/users", name: "users", component: UsersPage },
    {
      path: "/users/:id(\\d+)/update",
      name: "user-update",
      component: UserUpdatePage,
      props: (route) => ({ id: Number(route.params.id) }),
    },
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
