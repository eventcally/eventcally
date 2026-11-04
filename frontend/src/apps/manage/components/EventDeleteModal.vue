<script setup lang="ts">
import { BModal } from "bootstrap-vue-next";
import { useI18n } from "vue-i18n";
import type { components } from "@/api/schema";
import EventDeleteForm from "./EventDeleteForm.vue";

type Deleted = components["schemas"]["EventDeleted"];

// The delete confirmation of the event list: the content of the delete page in a modal.
defineProps<{ organizationId: number; eventId: number | null }>();
const show = defineModel<boolean>({ default: false });
const emit = defineEmits<{ deleted: [answer: Deleted] }>();

const { t } = useI18n();
</script>

<template>
  <BModal
    v-model="show"
    :title="t('Delete %(model_display_name)s', { model_display_name: t('Event') })"
    no-footer
  >
    <!-- Rendered only while shown: it loads the form of the chosen event when mounted. -->
    <EventDeleteForm
      v-if="show && eventId !== null"
      :organization-id="organizationId"
      :id="eventId"
      inline
      @deleted="(answer) => emit('deleted', answer)"
    />
  </BModal>
</template>
