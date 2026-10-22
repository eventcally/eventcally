<script setup lang="ts">
import { BModal } from "bootstrap-vue-next";
import { ref } from "vue";
import { useI18n } from "vue-i18n";
import { api } from "@/shared/api";
import { useNotify } from "@/shared/notify";

const props = defineProps<{ widget: { id: number; name: string } | null }>();
const show = defineModel<boolean>({ default: false });
const emit = defineEmits<{ deleted: [] }>();

const { t } = useI18n();
const notify = useNotify();
const busy = ref(false);
const error = ref<string | null>(null);

async function confirm() {
  if (!props.widget) return;
  busy.value = true;
  error.value = null;
  const { error: err } = await api.DELETE("/bff/manage/custom-widgets/{id}", {
    params: { path: { id: props.widget.id } },
  });
  busy.value = false;
  if (err) {
    error.value = err.message ?? t("Error");
    return;
  }
  notify.success(t("Widget successfully deleted"));
  show.value = false;
  emit("deleted");
}
</script>

<template>
  <BModal
    v-model="show"
    :title="t('Delete widget')"
    :ok-title="t('Delete')"
    ok-variant="danger"
    :cancel-title="t('Cancel')"
    :ok-disabled="busy"
    @ok.prevent="confirm"
  >
    <div v-if="error" class="alert alert-danger" role="alert">{{ error }}</div>
    <p class="mb-0">{{ t("Do you really want to delete the widget?") }}</p>
    <p v-if="widget" class="fw-bold mt-2 mb-0">{{ widget.name }}</p>
  </BModal>
</template>
