import {
  createRouter,
  createWebHistory,
  type RouteRecordRaw,
} from "vue-router";
import { boot } from "@/shared/boot";
import NotFoundPage from "./pages/NotFoundPage.vue";
import PlanningPage from "./pages/PlanningPage.vue";

export const routes: RouteRecordRaw[] = [
  { path: "/planning", name: "planning", component: PlanningPage },
  { path: "/:rest(.*)*", name: "not-found", component: NotFoundPage },
];

export const router = createRouter({
  history: createWebHistory(boot.base),
  routes,
});
