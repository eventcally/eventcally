import { mountApp } from "@/shared/boot";
import App from "./App.vue";
import { router } from "./router";

mountApp(App, { router });
