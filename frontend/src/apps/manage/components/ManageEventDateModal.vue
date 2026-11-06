<script setup lang="ts">
import { BModal } from "bootstrap-vue-next";
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import type { components } from "@/api/schema";
import { boot } from "@/shared/boot";
import { formatEventDate } from "@/shared/format";
import { manage, publicPages } from "@/shared/legacy";
import {
  publicStatusVariant,
  statusLabel,
  statusVariant,
  type ManageEventDate,
} from "../manageEventCalendar";

type Options = components["schemas"]["ManageEventListOptions"];

const props = defineProps<{
  row: ManageEventDate | null;
  organizationId: number;
  options: Options;
}>();
const emit = defineEmits<{ delete: [eventId: number] }>();
const visible = defineModel<boolean>({ default: false });

const { t } = useI18n();

const dateText = computed(() =>
  props.row ? formatEventDate(props.row.start, props.row.end, props.row.allday, boot.locale) : "",
);

function askDelete() {
  if (!props.row) return;
  visible.value = false;
  emit("delete", props.row.event.id);
}
</script>

<template>
  <BModal v-model="visible" :title="row?.event.name ?? ''" no-footer>
    <div v-if="row" data-test="details">
      <p class="mb-2"><i class="fa fa-fw me-2 fa-calendar"></i>{{ dateText }}</p>
      <p class="mb-2 d-flex flex-wrap gap-1">
        <span
          v-if="row.event.status"
          class="badge"
          :class="`text-bg-${statusVariant(row.event.status)}`"
          data-test="status"
          >{{ statusLabel(options.statuses, row.event.status) }}</span
        >
        <span
          class="badge"
          :class="`text-bg-${publicStatusVariant[row.event.public_status] ?? 'light'}`"
          data-test="public-status"
          >{{ statusLabel(options.public_statuses, row.event.public_status) }}</span
        >
      </p>
      <p v-if="row.event.organizer_name" class="mb-1">
        <i class="fa fa-fw me-2 fa-server"></i>{{ row.event.organizer_name }}
      </p>
      <p v-if="row.event.place_label" class="mb-1">
        <i class="fa fa-fw me-2 fa-map-marker"></i>{{ row.event.place_label }}
      </p>
      <p v-if="row.event.is_recurring" class="mb-1 text-body-secondary" data-test="recurring">
        <i class="fas fa-fw me-2 fa-history"></i
        >{{ t("The actions apply to the whole event with all its dates.") }}
      </p>

      <div class="d-flex flex-wrap justify-content-end gap-2 mt-3">
        <a class="btn btn-outline-secondary" :href="publicPages.eventDate(row.id)" data-test="view">{{
          t("View")
        }}</a>
        <a
          class="btn btn-outline-secondary"
          :href="manage.eventUpdate(organizationId, row.event.id)"
          data-test="edit"
          >{{ t("Edit") }}</a
        >
        <button type="button" class="btn btn-outline-danger" data-test="delete" @click="askDelete">
          {{ t("Delete") }}
        </button>
        <a
          v-if="options.can_request_reference"
          class="btn btn-outline-secondary"
          :href="manage.eventReferenceRequestCreate(organizationId, row.event.id)"
          data-test="request-reference"
          >{{ t("Request reference") }}</a
        >
        <a
          class="btn btn-outline-secondary"
          :href="publicPages.eventActions(row.event.id)"
          data-test="more"
          >{{ t("More") }}</a
        >
        <button type="button" class="btn btn-primary" @click="visible = false">
          {{ t("Close") }}
        </button>
      </div>
    </div>
  </BModal>
</template>
