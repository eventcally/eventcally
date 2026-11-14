<script setup lang="ts">
import { BModal } from "bootstrap-vue-next";
import { useI18n } from "vue-i18n";

export interface CalendarLinks {
  ics: string;
  google?: string | null;
}

defineProps<{ links: CalendarLinks }>();
const visible = defineModel<boolean>({ default: false });

const { t } = useI18n();
</script>

<template>
  <BModal v-model="visible" :title="t('Add to calendar')" no-footer centered>
    <div class="list-group">
      <a class="list-group-item list-group-item-action" :href="links.ics"
        ><i class="fab fa-fw me-2 fa-microsoft"></i>Outlook</a
      >
      <a
        v-if="links.google"
        class="list-group-item list-group-item-action"
        :href="links.google"
        target="_blank"
        rel="noopener"
        ><i class="fab fa-fw me-2 fa-google"></i>{{ t("Google calendar") }}</a
      >
      <a class="list-group-item list-group-item-action" :href="links.ics"
        ><i class="fab fa-fw me-2 fa-apple"></i>{{ t("Apple calendar") }}</a
      >
      <a class="list-group-item list-group-item-action" :href="links.ics"
        ><i class="fab fa-fw me-2 fa-yahoo"></i>{{ t("Yahoo calendar") }}</a
      >
      <a class="list-group-item list-group-item-action" :href="links.ics"
        ><i class="fa fa-fw me-2 fa-calendar"></i>{{ t("Other calendar") }}</a
      >
    </div>
  </BModal>
</template>
