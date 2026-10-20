<script setup lang="ts">
import { useI18n } from "vue-i18n";
import { api } from "@/shared/api";
import { useNotify } from "@/shared/notify";
import TypeToConfirmModal from "./TypeToConfirmModal.vue";

const props = defineProps<{ user: { id: number; email: string } | null }>();
const show = defineModel<boolean>({ default: false });
const emit = defineEmits<{ deleted: [] }>();

const { t } = useI18n();
const notify = useNotify();

async function confirm(email: string) {
  if (!props.user) return;
  const { error: err } = await api.DELETE("/bff/admin/users/{id}", {
    params: { path: { id: props.user.id } },
    body: { email },
  });
  if (err) {
    const fieldError = "errors" in err ? err.errors[0]?.msg : undefined;
    throw new Error(fieldError ?? err.message ?? t("Error"));
  }
  notify.success(t("User successfully deleted"));
}
</script>

<template>
  <TypeToConfirmModal
    v-model="show"
    :title="t('Delete user')"
    :ok-title="t('Delete user')"
    :subject="user?.email ?? null"
    :label="t('Email')"
    input-id="delete-user-email"
    :confirm="confirm"
    @done="emit('deleted')"
  />
</template>
