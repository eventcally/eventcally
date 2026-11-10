<script setup lang="ts">
import { useI18n } from "vue-i18n";

// The calendars of an organization as checkboxes; private ones carry a badge.
defineProps<{
  choices: { id: number; name: string; private?: boolean }[];
  idPrefix?: string;
  error?: string;
}>();
const model = defineModel<number[]>({ default: () => [] });

const { t } = useI18n();
</script>

<template>
  <div data-test="calendar-picker">
    <div v-for="choice in choices" :key="choice.id" class="form-check">
      <input
        :id="`${idPrefix ?? 'calendar'}-${choice.id}`"
        v-model="model"
        class="form-check-input"
        type="checkbox"
        :value="choice.id"
      />
      <label class="form-check-label" :for="`${idPrefix ?? 'calendar'}-${choice.id}`">
        {{ choice.name }}
        <span v-if="choice.private" class="badge text-bg-secondary ms-1">{{ t("Private") }}</span>
      </label>
    </div>
    <div v-if="error" class="invalid-feedback d-block" data-test="calendar-error">{{ error }}</div>
  </div>
</template>
