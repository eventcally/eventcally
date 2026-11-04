import { ref, type Ref } from "vue";
import { useI18n } from "vue-i18n";
import { errorMessage, mapFieldErrors } from "./apiError";
import { useNotify } from "./notify";

interface Answer {
  data?: { message?: string } | undefined;
  error?: unknown;
  response?: { ok: boolean };
}

/**
 * The state behind a `ConfirmModal` that acts on one row: `open(item)` shows it, `submit`
 * runs the BFF call, shows a 422 on the name field / any other error inside the modal and,
 * on success, a toast with the server's text, closes and reloads the list.
 */
export function useConfirmAction<T>(options: {
  call: (item: T, name: string | undefined) => Promise<Answer>;
  onDone: () => void | Promise<void>;
}) {
  const { t } = useI18n();
  const notify = useNotify();

  const item = ref<T | null>(null) as Ref<T | null>;
  const show = ref(false);
  const busy = ref(false);
  const error = ref<string | null>(null);
  const nameError = ref<string | undefined>();

  function open(next: T) {
    item.value = next;
    error.value = null;
    nameError.value = undefined;
    show.value = true;
  }

  async function submit(name?: string) {
    if (busy.value || item.value === null) return;
    busy.value = true;
    error.value = null;
    nameError.value = undefined;

    const { data, error: err, response } = await options.call(item.value, name);
    busy.value = false;

    if (response?.ok ?? !err) {
      if (data?.message) notify.success(data.message);
      show.value = false;
      await options.onDone();
      return;
    }

    const mapped = mapFieldErrors(err, ["name"]);
    if (mapped) {
      nameError.value = mapped.byKey.name;
      if (mapped.unmatched.length) error.value = mapped.unmatched.join(" ");
    } else {
      error.value = errorMessage(err, t("Error"));
    }
  }

  return { item, show, busy, error, nameError, open, submit };
}
