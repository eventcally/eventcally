import { computed, ref, watch, type Ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { errorMessage } from "@/shared/apiError";

interface PagedAnswer<T> {
  data?: T;
  error?: unknown;
}

/** Loads one page of a list; the page lives in `route.query.page`. */
export function usePagedList<T>(
  fetchPage: (page: number) => Promise<PagedAnswer<T>>,
  routeName: string,
  errorFallback: string,
  extraSources: Ref<unknown>[] = [],
) {
  const route = useRoute();
  const router = useRouter();

  const page = ref<T | null>(null) as Ref<T | null>;
  const loading = ref(false);
  const error = ref<string | null>(null);

  const currentPage = computed({
    get: () => Number(route.query.page ?? 1) || 1,
    set: (value: number) => {
      router.push({
        name: routeName,
        query: { ...route.query, page: String(value) },
      });
    },
  });

  async function load() {
    loading.value = true;
    error.value = null;
    const { data, error: err } = await fetchPage(currentPage.value);
    if (data) page.value = data;
    else error.value = errorMessage(err, errorFallback);
    loading.value = false;
  }

  watch([() => route.query, ...extraSources], load, { immediate: true });

  return { page, loading, error, currentPage, load };
}
