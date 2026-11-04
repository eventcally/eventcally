<script setup lang="ts">
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import ManageBreadcrumb from "@/shared/ManageBreadcrumb.vue";
import EventDeleteForm from "../components/EventDeleteForm.vue";

// Kept as a page: the public event pages link here.
const props = defineProps<{ organizationId: number; id: number }>();

const { t } = useI18n();

const title = computed(() =>
  t("Delete %(model_display_name)s", { model_display_name: t("Event") }),
);

function done(answer: { redirect_url: string }) {
  // The server flashed the success text for the list.
  window.location.assign(answer.redirect_url);
}
</script>

<template>
  <div>
    <ManageBreadcrumb
      :organization-id="props.organizationId"
      :items="[
        { label: t('Events'), to: { name: 'manage-events', params: { organizationId } } },
        { label: title },
      ]"
    />
    <EventDeleteForm :organization-id="organizationId" :id="id" @deleted="done" />
  </div>
</template>
