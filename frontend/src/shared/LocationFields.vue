<script setup lang="ts">
import { BFormGroup, BFormInput } from "bootstrap-vue-next";
import { useI18n } from "vue-i18n";
import PlaceLookup from "./PlaceLookup.vue";

export interface LocationValue {
  street: string;
  postalCode: string;
  city: string;
  state: string;
  latitude: number | null;
  longitude: number | null;
}

withDefaults(
  defineProps<{
    errors?: Record<string, string | undefined>;
    // The Google lookup on top (a form may place it elsewhere).
    lookup?: boolean;
    // Postal code and city are required (the place location is optional).
    required?: boolean;
  }>(),
  { lookup: true, required: true },
);
const model = defineModel<LocationValue>({ required: true });

const { t } = useI18n();

function set<K extends keyof LocationValue>(key: K, value: LocationValue[K]) {
  model.value = { ...model.value, [key]: value };
}

function toNumber(value: string | number | null | undefined): number | null {
  if (value === null || value === undefined || value === "") return null;
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}
</script>

<template>
  <div data-test="location-fields">
    <PlaceLookup v-if="lookup" @picked="model = $event.address" />

    <BFormGroup :label="t('Street')" label-for="location-street" class="mb-3"
      :state="errors?.street ? false : null" :invalid-feedback="errors?.street">
      <BFormInput id="location-street" :model-value="model.street" maxlength="255"
        :state="errors?.street ? false : null" @update:model-value="set('street', $event as string)" />
    </BFormGroup>
    <BFormGroup :label="t('State')" label-for="location-state" class="mb-3"
      :state="errors?.state ? false : null" :invalid-feedback="errors?.state">
      <BFormInput id="location-state" :model-value="model.state" maxlength="255"
        :state="errors?.state ? false : null" @update:model-value="set('state', $event as string)" />
    </BFormGroup>
    <BFormGroup :label="t('Latitude')" label-for="location-latitude" class="mb-3"
      :state="errors?.latitude ? false : null" :invalid-feedback="errors?.latitude">
      <BFormInput id="location-latitude" type="number" step="any" :model-value="model.latitude ?? ''"
        :state="errors?.latitude ? false : null" @update:model-value="set('latitude', toNumber($event))" />
    </BFormGroup>
    <BFormGroup :label="t('Longitude')" label-for="location-longitude" class="mb-3"
      :state="errors?.longitude ? false : null" :invalid-feedback="errors?.longitude">
      <BFormInput id="location-longitude" type="number" step="any" :model-value="model.longitude ?? ''"
        :state="errors?.longitude ? false : null" @update:model-value="set('longitude', toNumber($event))" />
    </BFormGroup>
    <BFormGroup :label="required ? `${t('Postal code')} *` : t('Postal code')" label-for="location-postalCode" class="mb-3"
      :state="errors?.postalCode ? false : null" :invalid-feedback="errors?.postalCode">
      <BFormInput id="location-postalCode" :model-value="model.postalCode" maxlength="10" :required="required"
        :state="errors?.postalCode ? false : null" @update:model-value="set('postalCode', $event as string)" />
    </BFormGroup>
    <BFormGroup :label="required ? `${t('City')} *` : t('City')" label-for="location-city" class="mb-3"
      :state="errors?.city ? false : null" :invalid-feedback="errors?.city">
      <BFormInput id="location-city" :model-value="model.city" maxlength="255" :required="required"
        :state="errors?.city ? false : null" @update:model-value="set('city', $event as string)" />
    </BFormGroup>
  </div>
</template>
