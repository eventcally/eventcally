<script setup lang="ts">
import { BModal } from "bootstrap-vue-next";
import { ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { api } from "@/shared/api";
import { useNotify } from "@/shared/notify";

const show = defineModel<boolean>({ default: false });

const { t } = useI18n();
const notify = useNotify();

const error = ref<string | null>(null);
const busy = ref(false);

watch(show, (open) => {
  if (open) error.value = null;
});

async function onOk(event: { preventDefault: () => void }) {
  event.preventDefault();
  if (busy.value) return;

  busy.value = true;
  error.value = null;
  const { error: err } = await api.POST("/bff/admin/settings/reset-tos-accepted");
  busy.value = false;

  if (err) {
    error.value = err.message ?? t("Error");
    return;
  }

  notify.success(t("Acceptance of terms of service and privacy reset"));
  show.value = false;
}
</script>

<template>
  <BModal
    v-model="show"
    :title="t('Reset acceptance of terms of service and privacy')"
    :ok-title="t('Reset')"
    :cancel-title="t('Cancel')"
    ok-variant="danger"
    :ok-disabled="busy"
    @ok="onOk"
  >
    <div v-if="error" class="alert alert-danger" role="alert">{{ error }}</div>
    <p class="mb-0">
      {{ t("All users have to accept the terms of service and privacy again.") }}
    </p>
  </BModal>
</template>
