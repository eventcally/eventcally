<script setup lang="ts">
import { useI18n } from "vue-i18n";

// The roles of a member (invitation) as checkboxes, like the old multi checkbox field.
defineProps<{
  choices: { name: string; title: string }[];
  idPrefix?: string;
  error?: string;
}>();
const model = defineModel<string[]>({ default: () => [] });

const { t } = useI18n();
</script>

<template>
  <div class="mb-3" data-test="roles">
    <label class="form-label d-block">{{ t("Roles") }}</label>
    <div v-for="choice in choices" :key="choice.name" class="form-check">
      <input
        :id="`${idPrefix ?? 'role'}-${choice.name}`"
        v-model="model"
        class="form-check-input"
        type="checkbox"
        :value="choice.name"
      />
      <label class="form-check-label" :for="`${idPrefix ?? 'role'}-${choice.name}`">{{
        choice.title
      }}</label>
    </div>
    <div v-if="error" class="invalid-feedback d-block" data-test="roles-error">{{ error }}</div>
  </div>
</template>
