<script setup lang="ts">
import { useI18n } from "vue-i18n";
import LabeledField from "./LabeledField.vue";

// The fields of an OAuth2 client: name, redirect URIs (one per line) and the scopes.
defineProps<{ scopeChoices: string[]; errors?: Record<string, string> }>();

const clientName = defineModel<string>("clientName", { required: true });
const redirectUris = defineModel<string>("redirectUris", { required: true });
const scopes = defineModel<string[]>("scopes", { required: true });

const { t } = useI18n();

function toggle(scope: string, checked: boolean) {
  scopes.value = checked
    ? [...scopes.value, scope]
    : scopes.value.filter((existing) => existing !== scope);
}
</script>

<template>
  <LabeledField
    :label="t('Client name')"
    label-for="client_name"
    :error="errors?.client_name"
    required
  >
    <input
      id="client_name"
      v-model="clientName"
      type="text"
      class="form-control"
      :class="{ 'is-invalid': errors?.client_name }"
    />
  </LabeledField>

  <LabeledField
    :label="t('Redirect URIs')"
    label-for="redirect_uris"
    :error="errors?.redirect_uris"
  >
    <textarea
      id="redirect_uris"
      v-model="redirectUris"
      class="form-control"
      :class="{ 'is-invalid': errors?.redirect_uris }"
      rows="3"
    ></textarea>
  </LabeledField>

  <LabeledField :label="t('Scopes')" :error="errors?.scopes">
    <div v-for="(scope, index) in scopeChoices" :key="scope" class="form-check">
      <input
        :id="`scope-${index}`"
        type="checkbox"
        class="form-check-input"
        :value="scope"
        :checked="scopes.includes(scope)"
        @change="toggle(scope, ($event.target as HTMLInputElement).checked)"
      />
      <label class="form-check-label" :for="`scope-${index}`">{{ scope }}</label>
    </div>
  </LabeledField>
</template>
