<script setup lang="ts">
import bootstrap5Plugin from "@fullcalendar/bootstrap5";
import FullCalendar from "@fullcalendar/vue3";
import dayGridPlugin from "@fullcalendar/vue3/daygrid";
import deLocale from "@fullcalendar/vue3/locales/de";
import timeGridPlugin from "@fullcalendar/vue3/timegrid";
import type { CalendarOptions, DatesSetInfo, EventClickInfo } from "@fullcalendar/vue3";
import { BModal } from "bootstrap-vue-next";
import { computed, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";
import { boot } from "@/shared/boot";
import type { CalendarSettings } from "@/shared/customWidget";
import EventWarningPills from "@/shared/EventWarningPills.vue";
import { formatEventDate } from "@/shared/format";
import { publicPages } from "@/shared/legacy";
import { trackAnalytics, usePageViewTracking, useWidgetSettings } from "../bridge";

import "@fullcalendar/vue3/skeleton.css";
import "@fullcalendar/bootstrap5/theme.css";

type EventDate = components["schemas"]["WidgetEventDate"];

const TOOLBAR_HEIGHT = 88;
const PER_PAGE = 50;
const VIEWS = { week: "timeGridWeek", month: "dayGridMonth" } as const;

const { t } = useI18n();
const settings = useWidgetSettings<CalendarSettings>();
usePageViewTracking();

const calendar = ref<InstanceType<typeof FullCalendar> | null>(null);
const rows = ref<EventDate[]>([]);
const title = ref("");
const range = ref<{ date_from: string; date_to: string } | null>(null);
const selected = ref<EventDate | null>(null);
const showDetails = ref(false);

let request = 0;

const localDate = (d: Date) => d.toLocaleDateString("sv"); // YYYY-MM-DD
const viewFor = (type: string | undefined) => VIEWS[type as keyof typeof VIEWS] ?? VIEWS.week;

const height = computed(() =>
  Math.max(200, (parseInt(String(settings.value?.iFrameHeight), 10) || 600) - TOOLBAR_HEIGHT),
);

const events = computed(() =>
  rows.value.map((row) => ({
    id: String(row.id),
    title: row.event.name,
    start: row.start,
    end: row.end ?? undefined,
    allDay: row.allday,
    extendedProps: { row },
  })),
);

const options = computed<CalendarOptions>(() => ({
  plugins: [bootstrap5Plugin, dayGridPlugin, timeGridPlugin],
  initialView: viewFor(settings.value?.calendarType),
  headerToolbar: false,
  locale: boot.locale === "de" ? deLocale : "en",
  firstDay: 1,
  height: height.value,
  nowIndicator: true,
  dayMaxEvents: true,
  moreLinkClick: "popover",
  eventColor: settings.value?.eventBackgroundColor,
  datesSet: (info: DatesSetInfo) => {
    const last = new Date(info.end.getTime());
    last.setDate(last.getDate() - 1);
    title.value = info.view.title;
    range.value = { date_from: localDate(info.start), date_to: localDate(last) };
    loadEvents();
  },
  eventClick: (info: EventClickInfo) => {
    info.jsEvent.preventDefault();
    selected.value = info.event.extendedProps.row as EventDate;
    showDetails.value = true;
  },
}));

async function loadEvents() {
  if (!range.value || !settings.value) return;
  const mine = ++request;
  const query: Record<string, string | number> = { ...range.value, per_page: PER_PAGE };
  if (settings.value.organizationId) query.organization_id = settings.value.organizationId;
  const { data } = await api.GET("/bff/public/widget/event-dates", {
    params: { query: query as never },
  });
  if (mine !== request || !data) return;
  rows.value = data.items;
  scrollToEarliestEvent();
}

function scrollToEarliestEvent() {
  if (settings.value?.calendarType !== "week") return;
  const hours = rows.value.filter((r) => !r.allday).map((r) => new Date(r.start).getHours());
  if (hours.length) calendar.value?.getApi().scrollToTime({ hours: Math.min(...hours) });
}

watch(
  () => settings.value?.calendarType,
  (type) => calendar.value?.getApi().changeView(viewFor(type)),
);
watch(
  () => settings.value?.organizationId,
  () => loadEvents(),
);

const dateText = computed(() =>
  selected.value
    ? formatEventDate(selected.value.start, selected.value.end, selected.value.allday, boot.locale)
    : "",
);
const showOrganizer = computed(() => {
  const event = selected.value?.event;
  return !!event?.organizer_name && event.organizer_name !== event.organization_name;
});

function openEventDate() {
  if (!selected.value) return;
  const url = `${location.origin}${publicPages.eventDate(selected.value.id)}`;
  trackAnalytics({ event: "linkClick", url });
  window.open(url);
}
</script>

<template>
  <div v-if="settings" class="calendar-widget p-2">
    <div class="d-flex align-items-center mb-2" style="height: 40px">
      <button
        type="button"
        class="btn btn-sm btn-outline-secondary me-1"
        :aria-label="t('Previous')"
        data-test="prev"
        @click="calendar?.getApi().prev()"
      >
        <i class="fas fa-chevron-left"></i>
      </button>
      <button
        type="button"
        class="btn btn-sm btn-outline-secondary me-3"
        :aria-label="t('Next')"
        data-test="next"
        @click="calendar?.getApi().next()"
      >
        <i class="fas fa-chevron-right"></i>
      </button>
      <h2 class="fs-5 mb-0" data-test="title">{{ title }}</h2>
    </div>

    <FullCalendar ref="calendar" :options="{ ...options, events }" />

    <BModal v-model="showDetails" :title="selected?.event.name" no-footer>
      <div v-if="selected" data-test="details">
        <p class="mb-2"><i class="fa fa-fw me-2 fa-calendar"></i>{{ dateText }}</p>
        <p class="mb-2"><EventWarningPills :event="selected.event" /></p>
        <p class="mb-1">
          <i class="fa fa-fw me-2 fa-database"></i>{{ selected.event.organization_name }}
        </p>
        <p v-if="showOrganizer" class="mb-1">
          <i class="fa fa-fw me-2 fa-server"></i>{{ selected.event.organizer_name }}
        </p>
        <p v-if="selected.event.place_name" class="mb-1">
          <i class="fa fa-fw me-2 fa-map-marker"></i>{{ selected.event.place_name }}
        </p>
        <div class="d-flex justify-content-end gap-2 mt-3">
          <button type="button" class="btn btn-secondary" @click="showDetails = false">
            {{ t("Close") }}
          </button>
          <button type="button" class="btn btn-primary" data-test="open" @click="openEventDate">
            {{ t("Details") }}
          </button>
        </div>
      </div>
    </BModal>
  </div>
</template>
