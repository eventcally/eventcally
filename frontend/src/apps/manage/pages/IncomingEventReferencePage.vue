<script setup lang="ts">
import { BOverlay } from "bootstrap-vue-next";
import { computed, onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";
import { errorMessage } from "@/shared/apiError";
import AuditLine from "@/shared/AuditLine.vue";
import CalendarAssignModal from "@/shared/CalendarAssignModal.vue";
import ConfirmModal from "@/shared/ConfirmModal.vue";
import { publicPages } from "@/shared/legacy";
import ManageBreadcrumb from "@/shared/ManageBreadcrumb.vue";
import ReadActions from "@/shared/ReadActions.vue";
import ReadProps from "@/shared/ReadProps.vue";
import type { RowAction } from "@/shared/RowActions.vue";
import { useConfirmAction } from "@/shared/useConfirmAction";
import EventReferenceRatingModal from "../components/EventReferenceRatingModal.vue";

type Reference = components["schemas"]["IncomingEventReferenceRead"];

const props = defineProps<{ organizationId: number; id: number }>();

const { t } = useI18n();

const reference = ref<Reference | null>(null);
const loading = ref(true);
const error = ref<string | null>(null);

async function load() {
  const { data, error: err } = await api.GET(
    "/bff/manage/organizations/{id}/incoming-event-references/{reference_id}",
    { params: { path: { id: props.organizationId, reference_id: props.id } } },
  );
  loading.value = false;

  if (data) reference.value = data;
  else error.value = errorMessage(err, t("Error"));
}

onMounted(load);

const modelName = computed(() => t("Incoming reference"));
const objectTitle = computed(() => `${t("Event reference")} ${props.id}`);

const showRating = ref(false);
const showCalendars = ref(false);

// Deleting leaves the page: the server flashes the text for the list (a full page load, so
// the Flask frame shows the flash).
const listUrl = computed(
  () => `/manage/admin_unit/${props.organizationId}/incoming_event_references`,
);

const confirm = useConfirmAction<Reference>({
  call: (item) =>
    api.POST("/bff/manage/organizations/{id}/incoming-event-references/{reference_id}/delete", {
      params: { path: { id: props.organizationId, reference_id: item.id } },
      body: { inline: false },
    }),
  onDone: () => window.location.assign(listUrl.value),
});

const actions = computed<RowAction[]>(() => {
  const result: RowAction[] = [];

  if (reference.value?.can_write) {
    result.push(
      { title: t("Edit"), onClick: () => (showRating.value = true) },
      { title: t("Delete"), onClick: () => reference.value && confirm.open(reference.value) },
    );
  }

  if (reference.value?.can_assign_calendars) {
    result.push({ title: t("Calendars…"), onClick: () => (showCalendars.value = true) });
  }

  if (reference.value) {
    result.push({ title: t("View event"), href: publicPages.event(reference.value.event_id) });
  }

  return result;
});
</script>

<template>
  <div>
    <ManageBreadcrumb
      :organization-id="organizationId"
      :items="[
        {
          label: t('Incoming references'),
          to: { name: 'incoming-event-references', params: { organizationId } },
        },
        { label: objectTitle },
      ]"
    />

    <div v-if="error" class="alert alert-danger" role="alert">{{ error }}</div>

    <BOverlay :show="loading">
      <template v-if="reference">
        <ReadActions :actions="actions" />

        <ReadProps
          :rows="[
            {
              label: t('Event'),
              value: reference.event_name,
              href: publicPages.event(reference.event_id),
            },
            { label: t('Rating'), value: reference.rating_text },
          ]"
        />
        <AuditLine :audit="reference.audit" />

        <EventReferenceRatingModal
          v-model="showRating"
          :organization-id="organizationId"
          :reference-id="reference.id"
          :rating="reference.rating ?? null"
          :choices="reference.rating_choices"
          @saved="load"
        />
        <CalendarAssignModal
          v-if="reference.can_assign_calendars"
          v-model="showCalendars"
          :organization-id="organizationId"
          :event-id="reference.event_id"
        />
        <ConfirmModal
          v-model="confirm.show.value"
          :title="t('Delete %(model_display_name)s', { model_display_name: modelName })"
          :confirm-title="t('Delete reference')"
          :instruction="t('Do you want to delete \'%(object_title)s\'?', { object_title: objectTitle })"
          :busy="confirm.busy.value"
          :error="confirm.error.value"
          @submit="confirm.submit"
        />
      </template>
    </BOverlay>
  </div>
</template>
