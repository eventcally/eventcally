<script setup lang="ts">
import { useI18n } from "vue-i18n";
import { api } from "@/shared/api";
import { useNotify } from "@/shared/notify";
import TypeToConfirmModal from "./TypeToConfirmModal.vue";

const props = defineProps<{ organization: { id: number; name: string } | null }>();
const show = defineModel<boolean>({ default: false });
const emit = defineEmits<{ deleted: [] }>();

const { t } = useI18n();
const notify = useNotify();

async function confirm(name: string) {
  if (!props.organization) return;
  const { error: err } = await api.DELETE("/bff/admin/organizations/{id}", {
    params: { path: { id: props.organization.id } },
    body: { name },
  });
  if (err) {
    const fieldError = "errors" in err ? err.errors[0]?.msg : undefined;
    throw new Error(fieldError ?? err.message ?? t("Error"));
  }
  notify.success(t("Organization successfully deleted"));
}
</script>

<template>
  <TypeToConfirmModal
    v-model="show"
    :title="t('Delete organization')"
    :ok-title="t('Delete organization')"
    :subject="organization?.name ?? null"
    :label="t('Name')"
    input-id="delete-organization-name"
    :confirm="confirm"
    @done="emit('deleted')"
  />
</template>
