import { createRouter, createWebHistory, type RouteRecordRaw } from "vue-router";
import { boot } from "@/shared/boot";
import CustomWidgetEditPage from "./pages/CustomWidgetEditPage.vue";
import CustomWidgetsPage from "./pages/CustomWidgetsPage.vue";
import ManageEventsPage from "./pages/ManageEventsPage.vue";
import NotFoundPage from "./pages/NotFoundPage.vue";
import OrganizationSettingsPage from "./pages/OrganizationSettingsPage.vue";
import PlanningPage from "./pages/PlanningPage.vue";

export const routes: RouteRecordRaw[] = [
  { path: "/planning", name: "planning", component: PlanningPage },
  {
    path: "/manage/admin_unit/:organizationId(\\d+)/custom-widgets",
    name: "custom-widgets",
    component: CustomWidgetsPage,
    props: (route) => ({ organizationId: Number(route.params.organizationId) }),
  },
  {
    path: "/manage/admin_unit/:organizationId(\\d+)/custom-widgets/create",
    name: "custom-widget-create",
    component: CustomWidgetEditPage,
    props: (route) => ({ organizationId: Number(route.params.organizationId) }),
  },
  {
    path: "/manage/admin_unit/:organizationId(\\d+)/custom-widgets/:id(\\d+)/update",
    name: "custom-widget-update",
    component: CustomWidgetEditPage,
    props: (route) => ({
      organizationId: Number(route.params.organizationId),
      id: Number(route.params.id),
    }),
  },
  {
    path: "/manage/admin_unit/:organizationId(\\d+)/events",
    name: "manage-events",
    component: ManageEventsPage,
    props: (route) => ({ organizationId: Number(route.params.organizationId) }),
  },
  {
    path: "/manage/admin_unit/:organizationId(\\d+)/update",
    name: "organization-settings",
    component: OrganizationSettingsPage,
    props: (route) => ({ organizationId: Number(route.params.organizationId) }),
  },
  { path: "/:rest(.*)*", name: "not-found", component: NotFoundPage },
];

export const router = createRouter({
  history: createWebHistory(boot.base),
  routes,
});
