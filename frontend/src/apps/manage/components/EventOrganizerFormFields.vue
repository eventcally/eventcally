<script setup lang="ts">
import { BFormGroup, BFormInput } from "bootstrap-vue-next";
import { computed, onBeforeUnmount, ref } from "vue";
import { useI18n } from "vue-i18n";
import { api } from "@/shared/api";
import ImageField from "@/shared/ImageField.vue";
import LocationFields from "@/shared/LocationFields.vue";
import type { EventOrganizerFormValue } from "../eventOrganizerForm";


type TextField = "url" | "email" | "phone" | "fax";

const props = withDefaults(
  defineProps<{
    organizationId: number;
    licenses: { id: number; name: string }[];
    // The organizer whose own name does not count as taken (update).
    excludeId?: number;
    // The stored name: an unchanged value needs no check.
    originalName?: string;
    // Prefix of the input ids (the fields in a modal next to another form).
    idPrefix?: string;
  }>(),
  { idPrefix: "" },
);

const form = defineModel<EventOrganizerFormValue>({ required: true });
const errors = defineModel<Record<string, string>>("errors", { required: true });
const logoPreview = defineModel<string | null>("logoPreview", { default: null });

const { t } = useI18n();

const CHECK_DELAY_MS = 300;
// Live availability of the name: the message when taken, "" when free, `null` unchecked.
const nameTaken = ref<string | null>(null);
let checkTimer: ReturnType<typeof setTimeout> | undefined;

const nameState = computed(() => {
  if (errors.value.name || nameTaken.value) return false;
  return form.value.name.trim() && nameTaken.value === "" ? true : null;
});

const textFields = computed<{ key: TextField; label: string; type: string }[]>(() => [
  { key: "url", label: t("Link URL"), type: "url" },
  { key: "email", label: t("Email"), type: "email" },
  { key: "phone", label: t("Phone"), type: "tel" },
  { key: "fax", label: t("Fax"), type: "tel" },
]);

function id(name: string) {
  return `${props.idPrefix}${name}`;
}

function set<K extends keyof EventOrganizerFormValue>(key: K, value: EventOrganizerFormValue[K]) {
  form.value = { ...form.value, [key]: value };
}

function fieldErrors(prefix: string): Record<string, string | undefined> {
  const result: Record<string, string | undefined> = {};
  for (const [key, message] of Object.entries(errors.value)) {
    if (key.startsWith(`${prefix}.`)) result[key.slice(prefix.length + 1)] = message;
  }
  return result;
}

function checkName(name: string) {
  clearTimeout(checkTimer);
  const value = name.trim();
  const rest = { ...errors.value };
  delete rest.name;
  errors.value = rest;
  nameTaken.value = null;

  if (!value || value === props.originalName) return;

  checkTimer = setTimeout(async () => {
    const { data } = await api.GET("/bff/manage/organizations/{id}/event-organizers/name-availability", {
      params: {
        path: { id: props.organizationId },
        query: { name: value, exclude_id: props.excludeId },
      },
    });
    // The field changed while the request was in flight.
    if (!data || form.value.name.trim() !== value) return;
    nameTaken.value = data.name_taken ? t("An organizer already exists with this name.") : "";
  }, CHECK_DELAY_MS);
}

function onName(value: string) {
  set("name", value);
  checkName(value);
}

onBeforeUnmount(() => clearTimeout(checkTimer));
</script>

<template>
  <div data-test="event-organizer-fields">
    <BFormGroup
      :label="`${t('Name')} *`"
      :label-for="id('name')"
      :state="nameState"
      :invalid-feedback="errors.name ?? nameTaken ?? undefined"
      class="mb-3"
    >
      <BFormInput
        :id="id('name')"
        :model-value="form.name"
        required
        maxlength="255"
        autocomplete="off"
        :state="nameState"
        @update:model-value="onName($event as string)"
      />
    </BFormGroup>

    <div class="card mb-4">
      <div class="card-header">{{ t("Location") }}</div>
      <div class="card-body">
        <LocationFields
          :model-value="form.location"
          :errors="fieldErrors('location')"
          :required="false"
          @update:model-value="set('location', $event)"
        />
      </div>
    </div>

    <div class="card mb-4">
      <div class="card-header">{{ t("Logo") }}</div>
      <div class="card-body">
        <ImageField
          v-model:preview="logoPreview"
          :model-value="form.logo"
          :licenses="licenses"
          :errors="fieldErrors('logo')"
          :id-prefix="idPrefix ? id('logo-') : undefined"
          @update:model-value="set('logo', $event)"
        />
      </div>
    </div>

    <BFormGroup
      v-for="field in textFields"
      :key="field.key"
      :label="field.label"
      :label-for="id(field.key)"
      :state="errors[field.key] ? false : null"
      :invalid-feedback="errors[field.key]"
      class="mb-3"
    >
      <BFormInput
        :id="id(field.key)"
        :model-value="form[field.key]"
        :type="field.type as 'url' | 'email' | 'tel'"
        maxlength="255"
        :state="errors[field.key] ? false : null"
        @update:model-value="set(field.key, $event as string)"
      />
    </BFormGroup>
  </div>
</template>
