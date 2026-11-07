<script setup lang="ts">
import { BButtonGroup, BSpinner } from "bootstrap-vue-next";
import { computed, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";
import {
  toManageCalendarEvent,
  type ManageEventDate,
  type ReferenceTarget,
} from "../manageEventCalendar";
import { type ManageEventFilter, toBffDateParams } from "../manageEventQuery";
import { earliestHour } from "../planning";
import ManageEventDateModal from "./ManageEventDateModal.vue";
import PlanningCalendar, { type CalendarRange, type CalendarView } from "./PlanningCalendar.vue";

type Options = components["schemas"]["ManageEventListOptions"];

const props = defineProps<{
  organizationId: number;
  filter: ManageEventFilter;
  options: Options;
}>();
const emit = defineEmits<{
  position: [position: { view: CalendarView; date: string }];
  delete: [eventId: number];
  deleteReference: [target: ReferenceTarget];
}>();

const { t } = useI18n();

const range = ref<CalendarRange | null>(null);
const rows = ref<ManageEventDate[]>([]);
const truncated = ref(false);
const loading = ref(false);
const error = ref<string | null>(null);
const selected = ref<ManageEventDate | null>(null);
const detailsVisible = ref(false);
const calendar = ref<InstanceType<typeof PlanningCalendar> | null>(null);

// Only the newest request may write its result: ranges change faster than responses arrive.
let request = 0;

const views: { view: CalendarView; label: () => string }[] = [
  { view: "timeGridDay", label: () => t("Day") },
  { view: "timeGridWeek", label: () => t("Week") },
  { view: "dayGridMonth", label: () => t("Month") },
];

const events = computed(() => rows.value.map(toManageCalendarEvent));

async function load() {
  if (!range.value) return;
  const current = ++request;
  loading.value = true;
  const { data, error: err } = await api.GET("/bff/manage/organizations/{id}/event-dates", {
    params: {
      path: { id: props.organizationId },
      query: toBffDateParams(props.filter, range.value),
    },
  });
  if (current !== request) return;
  loading.value = false;
  if (!data) {
    rows.value = [];
    truncated.value = false;
    error.value = err?.message ?? t("Error");
    return;
  }

  error.value = null;
  rows.value = data.items;
  truncated.value = data.truncated;
  const hour = earliestHour(data.items);
  if (hour !== null && range.value.view !== "dayGridMonth") calendar.value?.scrollToHour(hour);
}

function onRange(next: CalendarRange) {
  range.value = next;
  emit("position", { view: next.view, date: next.current });
  load();
}

function onSelect(props: Record<string, unknown>) {
  selected.value = props.row as ManageEventDate;
  detailsVisible.value = true;
}

// A changed filter reloads; the calendar position (also part of the filter) loads through `range`.
watch(
  () => JSON.stringify(toBffDateParams(props.filter, { date_from: "", date_to: "" })),
  () => load(),
);

defineExpose({ reload: load });
</script>

<template>
  <div class="manage-event-calendar">
    <div v-if="error" class="alert alert-danger" role="alert" data-test="calendar-error">
      {{ error }}
    </div>
    <div v-if="truncated" class="alert alert-warning" role="alert" data-test="truncated">
      {{
        t(
          "The maximum number of dates was loaded. Shorten the time period or refine the search for better results.",
        )
      }}
    </div>

    <div class="d-flex flex-wrap align-items-center gap-2 mb-3">
      <button
        type="button"
        class="btn btn-outline-secondary"
        data-test="today"
        @click="calendar?.today()"
      >
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

      <BButtonGroup class="ms-auto">
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

    <PlanningCalendar
      ref="calendar"
      :events="events"
      :initial-view="filter.calendar_view"
      :initial-date="filter.calendar_date || filter.date_from"
      @range="onRange"
      @select="onSelect"
    />

    <ManageEventDateModal
      v-model="detailsVisible"
      :row="selected"
      :organization-id="organizationId"
      :options="options"
      @delete="emit('delete', $event)"
      @delete-reference="emit('deleteReference', $event)"
    />
  </div>
</template>

<style scoped>
/* FullCalendar puts an event's `className` on its element. */
.manage-event-calendar :deep(.ec-cancelled) {
  text-decoration: line-through;
}

.manage-event-calendar :deep(.ec-status-info) {
  font-style: italic;
}

/* A referenced event of another organization. */
.manage-event-calendar :deep(.ec-reference) {
  outline: 2px dashed currentColor;
  outline-offset: -2px;
}
</style>
