import { mountApp } from "@/shared/boot";
import App from "./App.vue";
import { router } from "./router";
import { stripSourceParams } from "./sourceParams";

stripSourceParams();
mountApp(App, { router });
