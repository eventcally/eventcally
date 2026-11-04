import { onMounted } from "vue";
import { takeFlash } from "@/shared/flash";
import { useNotify } from "@/shared/notify";

/** Shows the success message a previous page left before `router.push` (a toast). */
export function useFlashNotice() {
  const notify = useNotify();
  onMounted(() => {
    const message = takeFlash();
    if (message) notify.success(message);
  });
}
