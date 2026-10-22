<script setup lang="ts">
import bootstrap5Plugin from "@fullcalendar/bootstrap5";
import FullCalendar from "@fullcalendar/vue3";
import dayGridPlugin from "@fullcalendar/vue3/daygrid";
import deLocale from "@fullcalendar/vue3/locales/de";
import timeGridPlugin from "@fullcalendar/vue3/timegrid";
import type { CalendarOptions, DatesSetInfo, EventClickInfo, EventInput } from "@fullcalendar/vue3";
import { computed, ref } from "vue";
import { boot } from "@/shared/boot";
import { rangeFromDatesSet, type CalendarEventProps } from "../planning";

import "@fullcalendar/vue3/skeleton.css";
import "@fullcalendar/bootstrap5/theme.css";

export type CalendarView = "dayGridMonth" | "timeGridWeek" | "timeGridDay";

export interface CalendarRange {
  date_from: string;
  date_to: string;
  title: string;
  view: CalendarView;
}

defineProps<{ events: EventInput[] }>();
const emit = defineEmits<{
  range: [range: CalendarRange];
  select: [props: CalendarEventProps];
}>();

const calendar = ref<InstanceType<typeof FullCalendar> | null>(null);

const options = computed<CalendarOptions>(() => ({
  // The Bootstrap 5 theme brings icon-font glyphs for its own toolbar, which is off here:
  // the page renders its own toolbar with Font Awesome icons.
  plugins: [bootstrap5Plugin, dayGridPlugin, timeGridPlugin],
  initialView: "dayGridMonth",
  headerToolbar: false,
  locale: boot.locale === "de" ? deLocale : "en",
  firstDay: 1,
  height: 800,
  navLinks: true,
  dayMaxEvents: true,
  moreLinkClick: "day",
  nowIndicator: true,
  datesSet: (info: DatesSetInfo) => {
    emit("range", {
      ...rangeFromDatesSet(info),
      title: info.view.title,
      view: info.view.type as CalendarView,
    });
  },
  eventClick: (info: EventClickInfo) => {
    info.jsEvent.preventDefault();
    emit("select", info.event.extendedProps as CalendarEventProps);
  },
}));

const api = () => calendar.value!.getApi();

defineExpose({
  prev: () => api().prev(),
  next: () => api().next(),
  today: () => api().today(),
  changeView: (view: CalendarView) => api().changeView(view),
  scrollToHour: (hour: number) => api().scrollToTime({ hours: hour }),
});
</script>

<template>
  <div data-test="calendar">
    <FullCalendar ref="calendar" :options="{ ...options, events }" />
  </div>
</template>
