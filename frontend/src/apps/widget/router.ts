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
  {
    // The iframe page customers embed; the URL is a contract (see legacyQuery.ts).
    path: "/organizations/:id(\\d+)/widget/eventdates",
    name: "eventdates",
    component: () => import("./pages/EventDatesWidget.vue"),
  },
];

export const router = createRouter({
  history: createWebHistory(boot.base),
  routes,
});
