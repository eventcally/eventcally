<script setup lang="ts">
import { BOverlay } from "bootstrap-vue-next";
import { computed, defineAsyncComponent, nextTick, onMounted, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { useRoute, useRouter } from "vue-router";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";
import AppPager from "@/shared/AppPager.vue";
import { boot } from "@/shared/boot";
import { useNotify } from "@/shared/notify";
import EventDateCard from "../components/EventDateCard.vue";
import EventDateSearchForm from "../components/EventDateSearchForm.vue";
import {
  type EventDateFilter,
  fromRouteQuery,
  toBffParams,
  toRouteQuery,
} from "../eventDateQuery";

// Leaflet is only loaded once the map is opened.
const EventDatesMap = defineAsyncComponent(() => import("../components/EventDatesMap.vue"));

type Options = components["schemas"]["EventDateSearchOptions"];
type Page = components["schemas"]["PublicEventDatePage"];

const { t } = useI18n();
const route = useRoute();
const router = useRouter();
const notify = useNotify();

const options = ref<Options | null>(null);
const filter = ref<EventDateFilter | null>(null);
const page = ref<Page | null>(null);
const loading = ref(false);
const error = ref<string | null>(null);
const busy = ref(false);
const showMap = ref(false);
const results = ref<HTMLElement | null>(null);
const map = ref<InstanceType<typeof EventDatesMap> | null>(null);

const defaults = computed(() => ({ date_from: options.value?.default_date_from ?? "" }));
const referencingId = computed(() => options.value?.referencing_organization?.id ?? null);

function idOf(value: unknown): number | undefined {
  const parsed = Number.parseInt(String(Array.isArray(value) ? value[0] : (value ?? "")), 10);
  return parsed > 0 ? parsed : undefined;
}

async function loadOptions() {
  const { data, error: err } = await api.GET("/bff/public/event-dates/options", {
    params: {
      query: {
        admin_unit_id: idOf(route.query.admin_unit_id),
        organizer_id: idOf(route.query.organizer_id),
      },
    },
  });
  if (data) options.value = data;
  else error.value = err?.message ?? t("Error");
  return Boolean(data);
}

async function search({ scroll = true }: { scroll?: boolean } = {}) {
  if (!filter.value) return;
  loading.value = true;
  error.value = null;
  const { data, error: err } = await api.GET("/bff/public/event-dates", {
    params: { query: toBffParams(filter.value) },
  });
  if (data) page.value = data;
  else {
    page.value = null;
    error.value = err?.message ?? t("Error");
  }
  loading.value = false;

  if (data && scroll) {
    await nextTick();
    results.value?.scrollIntoView?.({ behavior: "smooth", block: "start" });
  }
}

/** Applies the URL: reload the pickers' labels when the organization or organizer changed. */
async function apply({ scroll = true }: { scroll?: boolean } = {}) {
  const org = idOf(route.query.admin_unit_id) ?? null;
  const organizer = idOf(route.query.organizer_id) ?? null;
  const known = options.value;

  if (
    !known ||
    (org !== (known.organization?.id ?? null) && org !== null) ||
    (organizer !== (known.organizer?.id ?? null) && organizer !== null)
  ) {
    if (!(await loadOptions())) return;
  }

  filter.value = fromRouteQuery(route.query, defaults.value);
  await search({ scroll });
}

function onSearch(next: EventDateFilter) {
  const query = toRouteQuery(next, defaults.value);
  const same = JSON.stringify(query) === JSON.stringify(toRouteQuery(filter.value ?? next, defaults.value));
  filter.value = next;
  // An unchanged filter does not change the route, so search directly.
  if (same) search();
  else router.replace({ query });
}

function onPage(target: number) {
  if (filter.value) onSearch({ ...filter.value, page: target });
}

watch(
  () => route.query,
  () => {
    if (options.value) apply();
  },
);

onMounted(() => apply({ scroll: false }));

async function reference(eventId: number) {
  if (referencingId.value === null) return;
  busy.value = true;
  const { error: err } = await api.POST("/bff/manage/organizations/{id}/event-references", {
    params: { path: { id: referencingId.value } },
    body: { event_id: eventId },
  });
  if (err) notify.error(err.message ?? t("Error"));
  else notify.success(t("Reference successfully created"));
  await search({ scroll: false });
  busy.value = false;
}

async function unreference(referenceId: number) {
  busy.value = true;
  const { error: err } = await api.DELETE("/bff/manage/event-references/{id}", {
    params: { path: { id: referenceId } },
  });
  if (err) notify.error(err.message ?? t("Error"));
  else notify.success(t("Reference successfully deleted"));
  await search({ scroll: false });
  busy.value = false;
}

function toggleMap() {
  showMap.value = !showMap.value;
}

// The map component loads lazily, so a fly-to may have to wait for it.
let pendingFlyTo: [number, number] | null = null;

watch(map, (instance) => {
  if (instance && pendingFlyTo) {
    instance.flyTo(...pendingFlyTo);
    pendingFlyTo = null;
  }
});

async function flyTo(latitude: number, longitude: number) {
  showMap.value = true;
  await nextTick();
  document.getElementById("event-dates-map")?.scrollIntoView?.({ behavior: "smooth" });
  if (map.value) map.value.flyTo(latitude, longitude);
  else pendingFlyTo = [latitude, longitude];
}

function showInList(eventDateId: number) {
  const card = document.getElementById(`event_card_${eventDateId}`);
  if (!card) return;
  card.scrollIntoView?.({ behavior: "smooth", block: "center" });
  card.classList.add("highlight");
  setTimeout(() => card.classList.remove("highlight"), 1200);
}
</script>

<template>
  <div>
    <h1 class="mb-0">{{ t("Event Dates") }}</h1>

    <EventDateSearchForm
      v-if="filter && options"
      :filter="filter"
      :options="options"
      @search="onSearch"
      @toggle-map="toggleMap"
    />

    <div v-if="error" class="alert alert-danger m-3" role="alert">{{ error }}</div>

    <div class="row">
      <div v-if="showMap" id="event-dates-map" class="col-md mb-3">
        <EventDatesMap
          ref="map"
          :event-dates="page?.items ?? []"
          :locale="boot.locale"
          @show-in-list="showInList"
        />
      </div>
      <div class="col-md">
        <div id="result_container" ref="results">
          <BOverlay :show="loading">
            <div style="min-height: 300px">
              <EventDateCard
                v-for="eventDate in page?.items ?? []"
                :key="eventDate.id"
                :event-date="eventDate"
                :locale="boot.locale"
                :busy="busy"
                @fly-to="flyTo"
                @reference="reference"
                @unreference="unreference"
              />
              <p
                v-if="page && page.items.length === 0"
                class="text-center text-secondary"
                data-test="empty"
              >
                {{ t("No events found") }}
              </p>
            </div>
          </BOverlay>
          <AppPager
            v-if="page && page.total > 0"
            :page="page.page"
            :pages="page.pages"
            :total="page.total"
            @update:page="onPage"
          />
        </div>
      </div>
    </div>
  </div>
</template>
