<script setup lang="ts">
import { BFormInput, BModal } from "bootstrap-vue-next";
import { ref } from "vue";
import { useI18n } from "vue-i18n";
import { boot } from "@/shared/boot";
import { useNotify } from "@/shared/notify";

defineProps<{ url: string }>();
const visible = defineModel<boolean>({ default: false });

const { t } = useI18n();
const notify = useNotify();
const input = ref<InstanceType<typeof BFormInput> | null>(null);

async function copy(url: string) {
  try {
    await navigator.clipboard.writeText(url);
    notify.success(t("Link copied"));
  } catch {
    // Clipboard API unavailable (e.g. no HTTPS): let the user copy from the selected input.
    input.value?.$el?.select?.();
  }
}
</script>

<template>
  <BModal v-model="visible" :title="t('iCal calendar')" size="lg">
    <BFormInput ref="input" :model-value="url" readonly name="icalUrl" @focus="($event.target as HTMLInputElement).select()" />
    <template #footer>
      <a
        v-if="boot.docsUrl"
        class="btn btn-outline-info"
        :href="`${boot.docsUrl}/goto/ical-calendar`"
        target="_blank"
        rel="noopener noreferrer"
        >{{ t("Docs") }}</a
      >
      <button type="button" class="btn btn-primary" @click="copy(url)">{{ t("Copy link") }}</button>
      <a class="btn btn-secondary" :href="url">{{ t("Download") }}</a>
      <button type="button" class="btn btn-outline-secondary" @click="visible = false">
        {{ t("Close") }}
      </button>
    </template>
  </BModal>
</template>
