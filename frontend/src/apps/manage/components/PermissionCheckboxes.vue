<script setup lang="ts">
// Permissions (or event types) as checkboxes like the old multi checkbox field. With
// `disabled` they only show what is granted (the install and accept pages).
export interface CheckboxChoice {
  value: string;
  label: string;
}

defineProps<{
  choices: CheckboxChoice[];
  idPrefix: string;
  disabled?: boolean;
}>();
const model = defineModel<string[]>({ default: () => [] });
</script>

<template>
  <div>
    <div v-for="(choice, index) in choices" :key="choice.value" class="form-check">
      <input
        :id="`${idPrefix}-${index}`"
        v-model="model"
        class="form-check-input"
        type="checkbox"
        :value="choice.value"
        :disabled="disabled"
      />
      <label class="form-check-label" :for="`${idPrefix}-${index}`">{{ choice.label }}</label>
    </div>
  </div>
</template>
