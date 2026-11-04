<script setup lang="ts">
import { useI18n } from "vue-i18n";
import LabeledField from "./LabeledField.vue";

// The fields of an API key (user and, later, organization pages).
defineProps<{ errors?: Record<string, string> }>();

const name = defineModel<string>("name", { required: true });

const { t } = useI18n();
</script>

<template>
  <LabeledField :label="t('Name')" label-for="name" :error="errors?.name" required>
    <input
      id="name"
      v-model="name"
      type="text"
      class="form-control"
      :class="{ 'is-invalid': errors?.name }"
      autocomplete="off"
      role="presentation"
    />
  </LabeledField>
</template>
