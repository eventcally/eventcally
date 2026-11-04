<script setup lang="ts">
// A field as the legacy forms render it: the label, the description below it, then the
// input (the default slot) and its error.
defineProps<{
  label: string;
  labelFor?: string;
  description?: string;
  error?: string;
  required?: boolean;
  // The card header already names the field (legacy `label_hidden`).
  hideLabel?: boolean;
}>();
</script>

<template>
  <div class="mb-3" :class="{ 'is-invalid': error }">
    <label class="form-label mb-0" :class="{ 'visually-hidden': hideLabel }" :for="labelFor">{{ label }}<template v-if="required"> *</template></label>
    <div v-if="description" class="form-text mt-0 mb-1">{{ description }}</div>
    <slot />
    <div v-if="error" class="invalid-feedback d-block" data-test="field-error">{{ error }}</div>
  </div>
</template>
