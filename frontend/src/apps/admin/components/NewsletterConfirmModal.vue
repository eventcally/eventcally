<script setup lang="ts">
import { BModal } from "bootstrap-vue-next";
import { ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { api } from "@/shared/api";

const show = defineModel<boolean>({ default: false });
const emit = defineEmits<{ confirm: [] }>();

const { t } = useI18n();

const count = ref<number | null>(null);
const error = ref<string | null>(null);

watch(show, async (open) => {
  if (!open) return;

  count.value = null;
  error.value = null;
  const { data, error: err } = await api.GET("/bff/admin/newsletter");
  if (data) count.value = data.recipient_count;
  else error.value = err?.message ?? t("Error");
});

function onOk() {
  show.value = false;
  emit("confirm");
}
</script>

<template>
  <BModal
    v-model="show"
    :title="t('Send newsletter')"
    :ok-title="t('Send newsletter')"
    :cancel-title="t('Cancel')"
    :ok-disabled="!count"
    @ok="onOk"
  >
    <div v-if="error" class="alert alert-danger" role="alert">{{ error }}</div>
    <p v-else-if="count === 0" class="mb-0">{{ t("There are no recipients.") }}</p>
    <p v-else-if="count !== null" class="mb-0">
      {{ t("Send to %(count)d recipients?", { count }) }}
    </p>
  </BModal>
</template>
