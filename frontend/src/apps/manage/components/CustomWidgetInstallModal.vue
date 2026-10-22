<script setup lang="ts">
import { BButton, BModal } from "bootstrap-vue-next";
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import { installationBody, installationHeader } from "@/shared/customWidget";
import { useNotify } from "@/shared/notify";

const props = defineProps<{ widgetId: number | null }>();
const show = defineModel<boolean>({ default: false });

const { t } = useI18n();
const notify = useNotify();

const header = computed(() => installationHeader(location.origin));
const body = computed(() => (props.widgetId == null ? "" : installationBody(props.widgetId)));

async function copy(text: string) {
  await navigator.clipboard.writeText(text);
  notify.success(t("Copied"));
}
</script>

<template>
  <BModal v-model="show" :title="t('Installation')" size="lg" ok-only :ok-title="t('Close')">
    <p>{{ t("Copy the code below and paste it into your website.") }}</p>
    <p>{{ t("Paste the following code into the head of the page.") }}</p>
    <textarea
      class="form-control form-control-sm font-monospace"
      rows="4"
      readonly
      data-test="install-header"
      :value="header"
    ></textarea>
    <BButton size="sm" variant="outline-secondary" class="mt-2" @click="copy(header)">
      <i class="far fa-copy"></i> {{ t("Copy") }}
    </BButton>
    <p class="mt-3">
      {{ t("Paste the following code into the body of the page, where the widget should appear.") }}
    </p>
    <textarea
      class="form-control form-control-sm font-monospace"
      rows="2"
      readonly
      data-test="install-body"
      :value="body"
    ></textarea>
    <BButton size="sm" variant="outline-secondary" class="mt-2" @click="copy(body)">
      <i class="far fa-copy"></i> {{ t("Copy") }}
    </BButton>
  </BModal>
</template>
