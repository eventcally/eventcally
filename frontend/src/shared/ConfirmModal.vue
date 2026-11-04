<script setup lang="ts">
import { BModal } from "bootstrap-vue-next";
import { useI18n } from "vue-i18n";
import NameConfirmationForm from "./NameConfirmationForm.vue";

// A destructive action asked in a modal (delete / revoke / withdraw). With `confirmLabel`
// the old "type the name" form is embedded, otherwise a plain danger button confirms.
// The server answer is shown inside (`error` / `nameError`); the caller closes on success.
defineProps<{
  title: string;
  confirmTitle?: string;
  instruction?: string;
  confirmLabel?: string;
  busy?: boolean;
  error?: string | null;
  nameError?: string;
}>();
const show = defineModel<boolean>({ default: false });
const emit = defineEmits<{ submit: [name: string | undefined] }>();

const { t } = useI18n();
</script>

<template>
  <BModal
    v-model="show"
    :title="title"
    :ok-title="confirmTitle ?? title"
    ok-variant="danger"
    :cancel-title="t('Cancel')"
    :ok-disabled="busy"
    :no-footer="Boolean(confirmLabel)"
    @ok.prevent="emit('submit', undefined)"
  >
    <div v-if="error" class="alert alert-danger" role="alert" data-test="confirm-error">
      {{ error }}
    </div>
    <!-- Keyed by `show`: a reopened modal starts with an empty name. -->
    <NameConfirmationForm
      v-if="confirmLabel"
      :key="String(show)"
      :label="confirmLabel"
      :submit-label="confirmTitle ?? title"
      :error="nameError"
      :busy="busy"
      @submit="(value) => emit('submit', value)"
    >
      <p v-if="instruction">{{ instruction }}</p>
      <slot />
    </NameConfirmationForm>
    <template v-else>
      <p v-if="instruction" class="mb-0">{{ instruction }}</p>
      <slot />
    </template>
  </BModal>
</template>
