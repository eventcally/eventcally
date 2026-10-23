import {
  createRouter,
  createWebHistory,
  type RouteRecordRaw,
} from "vue-router";
import { boot } from "@/shared/boot";
import EventDatesPage from "./pages/EventDatesPage.vue";
import EventReportPage from "./pages/EventReportPage.vue";
import NotFoundPage from "./pages/NotFoundPage.vue";
import OrganizationPage from "./pages/OrganizationPage.vue";
import OrganizationsPage from "./pages/OrganizationsPage.vue";
import OrganizerPage from "./pages/OrganizerPage.vue";

export const routes: RouteRecordRaw[] = [
  {
    path: "/event/:id(\\d+)/report",
    name: "event-report",
    component: EventReportPage,
    props: (route) => ({ id: Number(route.params.id) }),
  },
  { path: "/eventdates", name: "event-dates", component: EventDatesPage },
  { path: "/organizations", name: "organizations", component: OrganizationsPage },
  {
    path: "/organizations/:id(\\d+)",
    name: "organization",
    component: OrganizationPage,
    props: (route) => ({ id: Number(route.params.id) }),
  },
  {
    path: "/organizers/:id(\\d+)",
    name: "organizer",
    component: OrganizerPage,
    props: (route) => ({ id: Number(route.params.id) }),
  },
  { path: "/:rest(.*)*", name: "not-found", component: NotFoundPage },
];

export const router = createRouter({
  history: createWebHistory(boot.base),
  routes,
});
