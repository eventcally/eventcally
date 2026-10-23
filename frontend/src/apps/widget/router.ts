import { createRouter, createWebHistory, type RouteRecordRaw } from "vue-router";
import { boot } from "@/shared/boot";

// Lazy: the calendar widget brings FullCalendar, which the search widget does not need.
export const routes: RouteRecordRaw[] = [
  {
    path: "/custom_widget/search",
    name: "search",
    component: () => import("./pages/SearchWidget.vue"),
  },
  {
    path: "/custom_widget/calendar",
    name: "calendar",
    component: () => import("./pages/CalendarWidget.vue"),
  },
];

export const router = createRouter({
  history: createWebHistory(boot.base),
  routes,
});
