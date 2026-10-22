<script setup lang="ts">
import { BModal } from "bootstrap-vue-next";
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import { boot } from "@/shared/boot";
import EventWarningPills from "@/shared/EventWarningPills.vue";
import { formatEventDate } from "@/shared/format";
import { publicPages } from "@/shared/legacy";
import type { CalendarEventProps } from "../planning";

const props = defineProps<{ selected: CalendarEventProps | null }>();
const visible = defineModel<boolean>({ default: false });

const { t } = useI18n();

const row = computed(() => (props.selected?.kind === "date" ? props.selected.row : null));
const external = computed(() => (props.selected?.kind === "external" ? props.selected : null));
const title = computed(() => row.value?.event.name ?? external.value?.item.name ?? "");
const dateText = computed(() => {
  if (row.value) {
    return formatEventDate(row.value.start, row.value.end, row.value.allday, boot.locale);
  }
  if (external.value) {
    const { start, end, allday } = external.value.item;
    return formatEventDate(start, end, allday, boot.locale);
  }
  return "";
});
const showOrganizer = computed(() => {
  const event = row.value?.event;
  return !!event?.organizer_name && event.organizer_name !== event.organization_name;
});
</script>

<template>
  <BModal v-model="visible" :title="title" no-footer>
    <div v-if="row || external" data-test="details">
      <p class="mb-2">
        <i class="fa fa-fw me-2 fa-calendar"></i>{{ dateText }}
      </p>

      <template v-if="row">
        <p v-if="row.event.has_status_info || row.event.booked_up || row.event.attendance_mode !== 'offline'" class="mb-2">
          <EventWarningPills :event="row.event" />
        </p>
        <p class="mb-1">
          <i class="fa fa-fw me-2 fa-database"></i>{{ row.event.organization_name }}
        </p>
        <p v-if="showOrganizer" class="mb-1">
          <i class="fa fa-fw me-2 fa-server"></i>{{ row.event.organizer_name }}
        </p>
        <p v-if="row.event.place_name" class="mb-1">
          <i class="fa fa-fw me-2 fa-map-marker"></i>{{ row.event.place_name }}
        </p>
      </template>

      <template v-else-if="external">
        <p v-if="external.item.location" class="mb-1">
          <i class="fa fa-fw me-2 fa-map-marker"></i>{{ external.item.location }}
        </p>
        <p v-if="external.item.description" class="mb-1" style="white-space: pre-line">
          {{ external.item.description }}
        </p>
        <p class="mb-1 text-body-secondary">
          <i class="fa fa-fw me-2 fa-calendar-alt"></i>{{ external.calendar.title }}
        </p>
      </template>
    </div>

    <div class="d-flex justify-content-end gap-2 mt-3">
      <a
        v-if="row"
        class="btn btn-primary"
        :href="publicPages.eventDate(row.id)"
        target="_blank"
        rel="noopener noreferrer"
        data-test="view"
        >{{ t("View") }}</a
      >
      <button type="button" class="btn btn-outline-secondary" @click="visible = false">
        {{ t("Close") }}
      </button>
    </div>
  </BModal>
</template>
