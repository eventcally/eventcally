<script setup lang="ts">
import { BButtonGroup, BSpinner } from "bootstrap-vue-next";
import { computed, onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";
import { boot } from "@/shared/boot";
import ExternalCalendarsModal from "../components/ExternalCalendarsModal.vue";
import PlanningCalendar, { type CalendarRange, type CalendarView } from "../components/PlanningCalendar.vue";
import PlanningEventDetailsModal from "../components/PlanningEventDetailsModal.vue";
import PlanningFilterModal from "../components/PlanningFilterModal.vue";
import {
  earliestHour,
  emptyFilter,
  filterToQuery,
  toCalendarEvent,
  toExternalEvent,
  type CalendarEventProps,
  type ExternalCalendarEvent,
  type PlanningEventDate,
  type PlanningFilter,
} from "../planning";

type PlanningOptions = components["schemas"]["PlanningOptions"];

const { t } = useI18n();

const options = ref<PlanningOptions | null>(null);
const loadError = ref<string | null>(null);
const filter = ref<PlanningFilter>(emptyFilter());
const range = ref<CalendarRange | null>(null);
const rows = ref<PlanningEventDate[]>([]);
const truncated = ref(false);
const loading = ref(false);
const activeCalendars = ref<string[]>([]);
const externalItems = ref<Record<string, ExternalCalendarEvent[]>>({});
const externalFailed = ref<string[]>([]);
const filterVisible = ref(false);
const externalVisible = ref(false);
const detailsVisible = ref(false);
const selected = ref<CalendarEventProps | null>(null);
const calendar = ref<InstanceType<typeof PlanningCalendar> | null>(null);

// Only the newest request may write its result: ranges change faster than responses arrive.
let datesRequest = 0;
let externalRequest = 0;

const views: { view: CalendarView; label: () => string }[] = [
  { view: "timeGridDay", label: () => t("Day") },
  { view: "timeGridWeek", label: () => t("Week") },
  { view: "dayGridMonth", label: () => t("Month") },
];

const calendars = computed(() =>
  (options.value?.external_calendars ?? []).map((c) => ({
    ...c,
    active: activeCalendars.value.includes(c.url),
  })),
);

const events = computed(() => [
  ...rows.value.map(toCalendarEvent),
  ...calendars.value
    .filter((c) => c.active)
    .flatMap((c) =>
      (externalItems.value[c.url] ?? []).map((item, index) => toExternalEvent(item, c, index)),
    ),
]);

const docsUrl = computed(() => (boot.docsUrl ? `${boot.docsUrl}/goto/event-planning` : null));

async function loadOptions() {
  const { data, error } = await api.GET("/bff/manage/planning");
  if (!data) {
    loadError.value = error?.message ?? t("Error");
    return;
  }
  options.value = data;
  activeCalendars.value = data.external_calendars.filter((c) => c.active).map((c) => c.url);
}

async function loadDates() {
  if (!range.value) return;
  const request = ++datesRequest;
  loading.value = true;
  const { data } = await api.GET("/bff/manage/planning/event-dates", {
    params: {
      query: {
        date_from: range.value.date_from,
        date_to: range.value.date_to,
        ...filterToQuery(filter.value),
      },
    },
  });
  if (request !== datesRequest) return;
  loading.value = false;
  if (!data) return;

  rows.value = data.items;
  truncated.value = data.truncated;
  const hour = earliestHour(data.items);
  if (hour !== null && range.value.view !== "dayGridMonth") calendar.value?.scrollToHour(hour);
}

async function loadExternal() {
  if (!range.value) return;
  const request = ++externalRequest;
  const { date_from, date_to } = range.value;
  const failed: string[] = [];
  const result: Record<string, ExternalCalendarEvent[]> = {};

  await Promise.all(
    activeCalendars.value.map(async (url) => {
      const { data } = await api.GET("/bff/manage/planning/external-calendar-events", {
        params: { query: { url, date_from, date_to } },
      });
      if (data) result[url] = data.items;
      else failed.push(url);
    }),
  );
  if (request !== externalRequest) return;

  externalItems.value = result;
  externalFailed.value = failed;
}

function onRange(next: CalendarRange) {
  range.value = next;
  loadDates();
  loadExternal();
}

function onFilter(next: PlanningFilter) {
  filter.value = next;
  loadDates();
}

function onExternalApply(active: string[]) {
  const changed = active.join("\n") !== activeCalendars.value.join("\n");
  activeCalendars.value = active;
  if (changed) loadExternal();
}

function onSelect(props: CalendarEventProps) {
  selected.value = props;
  detailsVisible.value = true;
}

onMounted(loadOptions);
</script>

<template>
  <div>
    <div class="d-flex align-items-center mb-3">
      <h1 class="my-0">{{ t("Event Planning") }}</h1>
      <a
        v-if="docsUrl"
        class="ms-3 text-decoration-none"
        :href="docsUrl"
        target="_blank"
        rel="noopener noreferrer"
        :title="t('Docs')"
        ><i class="fa fa-question-circle"></i
      ></a>
    </div>

    <div v-if="loadError" class="alert alert-danger" role="alert">{{ loadError }}</div>

    <template v-else-if="options">
      <div
        v-if="truncated"
        class="alert alert-warning"
        role="alert"
        data-test="truncated"
      >
        {{
          t(
            "The maximum number of dates was loaded. Shorten the time period or refine the search for better results.",
          )
        }}
      </div>
      <div
        v-if="externalFailed.length"
        class="alert alert-warning"
        role="alert"
        data-test="external-failed"
      >
        {{ t("An external calendar could not be loaded.") }}
      </div>

      <div class="d-flex flex-wrap align-items-center gap-2 mb-3">
        <button type="button" class="btn btn-outline-secondary" @click="calendar?.today()">
          {{ t("Today") }}
        </button>
        <BButtonGroup>
          <button
            type="button"
            class="btn btn-outline-secondary"
            :aria-label="t('Previous')"
            data-test="prev"
            @click="calendar?.prev()"
          >
            <i class="fa fa-chevron-left"></i>
          </button>
          <button
            type="button"
            class="btn btn-outline-secondary"
            :aria-label="t('Next')"
            data-test="next"
            @click="calendar?.next()"
          >
            <i class="fa fa-chevron-right"></i>
          </button>
        </BButtonGroup>

        <h2 class="h4 my-0 ms-2" data-test="title">{{ range?.title }}</h2>
        <small class="text-body-secondary" data-test="count">{{
          t("%(count)d event dates", { count: rows.length })
        }}</small>
        <BSpinner v-if="loading" small data-test="loading" />

        <div class="ms-auto d-flex flex-wrap gap-2">
          <button
            type="button"
            class="btn btn-outline-secondary"
            data-test="filter"
            @click="filterVisible = true"
          >
            <i class="fa fa-filter me-1"></i>{{ t("Filter") }}
          </button>
          <button
            v-if="options.external_calendars.length"
            type="button"
            class="btn btn-outline-secondary"
            data-test="external"
            @click="externalVisible = true"
          >
            <i class="fa fa-calendar-alt me-1"></i>{{ t("External calendars") }}
          </button>
          <BButtonGroup>
            <button
              v-for="v in views"
              :key="v.view"
              type="button"
              class="btn btn-outline-secondary"
              :class="{ active: range?.view === v.view }"
              :data-test="`view-${v.view}`"
              @click="calendar?.changeView(v.view)"
            >
              {{ v.label() }}
            </button>
          </BButtonGroup>
        </div>
      </div>

      <PlanningCalendar ref="calendar" :events="events" @range="onRange" @select="onSelect" />

      <PlanningFilterModal
        v-model="filterVisible"
        :categories="options.categories"
        :distances="options.distances"
        :filter="filter"
        @apply="onFilter"
      />
      <ExternalCalendarsModal
        v-model="externalVisible"
        :calendars="calendars"
        @apply="onExternalApply"
      />
      <PlanningEventDetailsModal v-model="detailsVisible" :selected="selected" />
    </template>
  </div>
</template>
