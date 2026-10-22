<script setup lang="ts">
import { useI18n } from "vue-i18n";

defineProps<{
  event: {
    public_status?: string | null;
    status?: string | null;
    booked_up?: boolean | null;
    attendance_mode?: string | null;
  };
}>();

const { t } = useI18n();
</script>

<template>
  <span class="event-warning-pills">
    <span
      v-if="event.public_status === 'draft'"
      class="badge rounded-pill text-bg-dark me-1"
      >{{ t("EventPublicStatus.draft") }}</span
    >
    <span
      v-else-if="event.public_status === 'planned'"
      class="badge rounded-pill text-bg-dark me-1"
      >{{ t("EventPublicStatus.planned") }}</span
    >
    <span
      v-if="event.status === 'cancelled'"
      class="badge rounded-pill text-bg-warning me-1"
      >{{ t("EventStatus.cancelled") }}</span
    >
    <span
      v-else-if="event.status === 'movedOnline'"
      class="badge rounded-pill text-bg-warning me-1"
      >{{ t("EventStatus.movedOnline") }}</span
    >
    <span
      v-else-if="event.status === 'postponed'"
      class="badge rounded-pill text-bg-warning me-1"
      >{{ t("EventStatus.postponed") }}</span
    >
    <span
      v-else-if="event.status === 'rescheduled'"
      class="badge rounded-pill text-bg-warning me-1"
      >{{ t("EventStatus.rescheduled") }}</span
    >
    <span v-if="event.booked_up" class="badge rounded-pill text-bg-warning me-1">{{
      t("Booked up")
    }}</span>
    <span
      v-if="event.attendance_mode === 'online'"
      class="badge rounded-pill text-bg-info me-1"
      >{{ t("EventAttendanceMode.online") }}</span
    >
    <span
      v-else-if="event.attendance_mode === 'mixed'"
      class="badge rounded-pill text-bg-info me-1"
      >{{ t("EventAttendanceMode.mixed") }}</span
    >
  </span>
</template>
