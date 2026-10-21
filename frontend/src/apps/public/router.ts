import {
  createRouter,
  createWebHistory,
  type RouteRecordRaw,
} from "vue-router";
import { boot } from "@/shared/boot";
import EventReportPage from "./pages/EventReportPage.vue";
import NotFoundPage from "./pages/NotFoundPage.vue";

export const routes: RouteRecordRaw[] = [
  {
    path: "/event/:id(\\d+)/report",
    name: "event-report",
    component: EventReportPage,
    props: (route) => ({ id: Number(route.params.id) }),
  },
  { path: "/:rest(.*)*", name: "not-found", component: NotFoundPage },
];

export const router = createRouter({
  history: createWebHistory(boot.base),
  routes,
});
