<script setup lang="ts">
import { BFormGroup, BFormInput, BFormTextarea } from "bootstrap-vue-next";
import { computed, onBeforeUnmount, ref } from "vue";
import { useI18n } from "vue-i18n";
import { api } from "@/shared/api";
import ImageField from "@/shared/ImageField.vue";
import LocationFields, { type LocationValue } from "@/shared/LocationFields.vue";
import PlaceLookup from "@/shared/PlaceLookup.vue";
import type { EventPlaceFormValue } from "../eventPlaceForm";


const props = withDefaults(
  defineProps<{
    organizationId: number;
    licenses: { id: number; name: string }[];
    // The place whose own name does not count as taken (update).
    excludeId?: number;
    // The stored name: an unchanged value needs no check.
    originalName?: string;
    // Prefix of the input ids (the fields in a modal next to another form).
    idPrefix?: string;
  }>(),
  { idPrefix: "" },
);

const form = defineModel<EventPlaceFormValue>({ required: true });
const errors = defineModel<Record<string, string>>("errors", { required: true });
const photoPreview = defineModel<string | null>("photoPreview", { default: null });

const { t } = useI18n();

const CHECK_DELAY_MS = 300;
// Live availability of the name: the message when taken, "" when free, `null` unchecked.
const nameTaken = ref<string | null>(null);
let checkTimer: ReturnType<typeof setTimeout> | undefined;

const nameState = computed(() => {
  if (errors.value.name || nameTaken.value) return false;
  return form.value.name.trim() && nameTaken.value === "" ? true : null;
});

function id(name: string) {
  return `${props.idPrefix}${name}`;
}

function set<K extends keyof EventPlaceFormValue>(key: K, value: EventPlaceFormValue[K]) {
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
    const { data } = await api.GET("/bff/manage/organizations/{id}/event-places/name-availability", {
      params: {
        path: { id: props.organizationId },
        query: { name: value, exclude_id: props.excludeId },
      },
    });
    // The field changed while the request was in flight.
    if (!data || form.value.name.trim() !== value) return;
    nameTaken.value = data.name_taken ? t("A place already exists with this name.") : "";
  }, CHECK_DELAY_MS);
}

function onName(value: string) {
  set("name", value);
  checkName(value);
}

function onPicked(place: { address: LocationValue; main_text: string | null }) {
  // Picking a place always overwrites the name (one update: the model is a prop).
  form.value = {
    ...form.value,
    location: place.address,
    ...(place.main_text ? { name: place.main_text } : {}),
  };
  if (place.main_text) checkName(place.main_text);
}

onBeforeUnmount(() => clearTimeout(checkTimer));
</script>

<template>
  <div data-test="event-place-fields">
    <PlaceLookup @picked="onPicked" />

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
          :lookup="false"
          :required="false"
          @update:model-value="set('location', $event)"
        />
      </div>
    </div>

    <div class="card mb-4">
      <div class="card-header">{{ t("Photo") }}</div>
      <div class="card-body">
        <ImageField
          v-model:preview="photoPreview"
          :model-value="form.photo"
          :licenses="licenses"
          :errors="fieldErrors('photo')"
          :id-prefix="idPrefix ? id('photo-') : undefined"
          @update:model-value="set('photo', $event)"
        />
      </div>
    </div>

    <BFormGroup
      :label="t('Link URL')"
      :label-for="id('url')"
      :state="errors.url ? false : null"
      :invalid-feedback="errors.url"
      class="mb-3"
    >
      <BFormInput
        :id="id('url')"
        :model-value="form.url"
        type="url"
        maxlength="255"
        :state="errors.url ? false : null"
        @update:model-value="set('url', $event as string)"
      />
    </BFormGroup>

    <BFormGroup :label="t('Description')" :label-for="id('description')" class="mb-3">
      <BFormTextarea
        :id="id('description')"
        :model-value="form.description"
        rows="2"
        @update:model-value="set('description', $event as string)"
      />
    </BFormGroup>
  </div>
</template>
