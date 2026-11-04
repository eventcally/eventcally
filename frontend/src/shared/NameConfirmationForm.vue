<script setup lang="ts">
import { BButton, type ButtonVariant } from "bootstrap-vue-next";
import { ref } from "vue";
import LabeledField from "./LabeledField.vue";

// "Type the name to confirm": the old delete / leave / account deletion forms. The server
// compares the value; its 422 arrives as `error`.
withDefaults(
  defineProps<{
    label: string;
    submitLabel: string;
    submitVariant?: ButtonVariant;
    inputId?: string;
    inputType?: string;
    error?: string;
    busy?: boolean;
  }>(),
  { submitVariant: "danger", inputId: "name", inputType: "text" },
);

const emit = defineEmits<{ submit: [value: string] }>();

const value = ref("");
</script>

<template>
  <form data-test="confirmation-form" @submit.prevent="emit('submit', value)">
    <slot />
    <LabeledField :label="label" :label-for="inputId" :error="error" required>
      <input
        :id="inputId"
        v-model="value"
        :type="inputType"
        class="form-control"
        :class="{ 'is-invalid': error }"
        autocomplete="off"
        role="presentation"
        required
      />
    </LabeledField>
    <BButton id="submit" type="submit" :variant="submitVariant" :disabled="busy">
      {{ submitLabel }}
    </BButton>
  </form>
</template>
