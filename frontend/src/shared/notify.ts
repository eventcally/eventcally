import { useToast } from "bootstrap-vue-next";

const AUTO_HIDE_MS = 5000;

/** Success / error feedback as toasts; rendered by the `BOrchestrator` in the app root. */
export function useNotify() {
  const toast = useToast();

  const show = (body: string, variant: "success" | "danger") =>
    toast.create({
      body,
      variant,
      position: "top-end",
      modelValue: AUTO_HIDE_MS,
      closeClass: "btn-close-white",
      progressProps: { variant: "light" },
    });

  return {
    success: (body: string) => show(body, "success"),
    error: (body: string) => show(body, "danger"),
  };
}
